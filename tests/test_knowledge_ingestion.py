import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import json

import pytest

import tools.knowledge_ingestion as ingestion

class FakeResponse:
    def __init__(
        self,
        content: bytes,
        content_type: str = "text/markdown",
        status_code: int = 200,
        headers: dict | None = None,
    ):
        self.content = content
        self.status_code = status_code

        self.headers = {
            "Content-Type": content_type,
            "Content-Length": str(len(content)),
        }

        if headers:
            self.headers.update(headers)

        self.is_redirect = False
        self.is_permanent_redirect = False

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(
                f"HTTP {self.status_code}"
            )

    def iter_content(self, chunk_size=64 * 1024):
        yield self.content

    def close(self):
        pass


@pytest.fixture
def isolated_environment(tmp_path, monkeypatch):
    external_root = tmp_path / "knowledge" / "external"
    manifest_path = external_root / "sources.json"

    external_root.mkdir(parents=True)

    manifest_path.write_text(
        json.dumps({"sources": []}),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        ingestion,
        "PROJECT_ROOT",
        tmp_path,
    )

    monkeypatch.setattr(
        ingestion,
        "EXTERNAL_ROOT",
        external_root,
    )

    monkeypatch.setattr(
        ingestion,
        "MANIFEST_PATH",
        manifest_path,
    )

    return tmp_path, external_root, manifest_path


def test_http_url_rejected():
    with pytest.raises(ValueError, match="HTTPS"):
        ingestion._validate_url(
            "http://example.com"
        )


def test_localhost_rejected():
    with pytest.raises(
        ValueError,
        match="Localhost",
    ):
        ingestion._validate_url(
            "https://localhost"
        )


def test_loopback_ip_rejected():
    with pytest.raises(
        ValueError,
        match="Unsafe IP",
    ):
        ingestion._validate_url(
            "https://127.0.0.1"
        )


def test_private_ip_rejected():
    with pytest.raises(
        ValueError,
        match="Unsafe IP",
    ):
        ingestion._validate_url(
            "https://192.168.1.10"
        )


def test_valid_https_hostname():
    # This only tests URL validation.
    # Network access is not performed here.
    parsed = ingestion._validate_url(
        "https://example.com/docs/test.md"
    )

    assert parsed.scheme == "https"
    assert parsed.hostname == "example.com"


def test_unsupported_content_type(
    isolated_environment,
    monkeypatch,
):
    response = FakeResponse(
        b"binary data",
        content_type="application/pdf",
    )

    monkeypatch.setattr(
        ingestion,
        "_download",
        lambda url: (
            response,
            url,
        ),
    )

    result = ingestion.add_knowledge_source(
        "https://example.com/file.pdf"
    )

    assert "unsupported content type" in result.lower()


def test_markdown_ingestion(
    isolated_environment,
    monkeypatch,
):
    content = b"""# Test Documentation

RuneStone uses PostgreSQL.

The database stores application records.
"""

    response = FakeResponse(
        content,
        content_type="text/markdown",
    )

    monkeypatch.setattr(
        ingestion,
        "_download",
        lambda url: (
            response,
            url,
        ),
    )

    # Avoid requiring FAISS/model loading during this unit test.
    class FakeIndex:
        def ensure_current(self):
            pass

    monkeypatch.setattr(
        ingestion,
        "KnowledgeIndex",
        FakeIndex,
        raising=False,
    )

    result = ingestion.add_knowledge_source(
        "https://example.com/database.md"
    )

    assert "Successfully ingested" in result

    files = list(
        isolated_environment[1].glob("*")
    )

    source_files = [
        path
        for path in files
        if path.name != "sources.json"
    ]

    assert len(source_files) == 1

    saved_text = source_files[0].read_text(
        encoding="utf-8"
    )

    assert "RuneStone uses PostgreSQL." in saved_text


def test_html_ingestion(
    isolated_environment,
    monkeypatch,
):
    html = b"""
    <html>
        <head>
            <title>Test</title>
            <script>
                console.log("should disappear");
            </script>
        </head>
        <body>
            <h1>RuneStone</h1>
            <p>Uses Docker sandboxing.</p>
        </body>
    </html>
    """

    response = FakeResponse(
        html,
        content_type="text/html",
    )

    monkeypatch.setattr(
        ingestion,
        "_download",
        lambda url: (
            response,
            url,
        ),
    )

    class FakeIndex:
        def ensure_current(self):
            pass

    monkeypatch.setattr(
        ingestion,
        "KnowledgeIndex",
        FakeIndex,
        raising=False,
    )

    result = ingestion.add_knowledge_source(
        "https://example.com/sandbox"
    )

    assert "Successfully ingested" in result

    source_files = [
        path
        for path in isolated_environment[1].glob("*")
        if path.name != "sources.json"
    ]

    assert len(source_files) == 1

    saved_text = source_files[0].read_text(
        encoding="utf-8"
    )

    assert "RuneStone" in saved_text
    assert "Docker sandboxing" in saved_text
    assert "should disappear" not in saved_text


def test_manifest_is_updated(
    isolated_environment,
    monkeypatch,
):
    content = b"# Test\n\nSome knowledge."

    response = FakeResponse(
        content,
        content_type="text/markdown",
    )

    monkeypatch.setattr(
        ingestion,
        "_download",
        lambda url: (
            response,
            url,
        ),
    )

    class FakeIndex:
        def ensure_current(self):
            pass

    monkeypatch.setattr(
        ingestion,
        "KnowledgeIndex",
        FakeIndex,
        raising=False,
    )

    url = "https://example.com/test.md"

    ingestion.add_knowledge_source(url)

    manifest = json.loads(
        isolated_environment[2].read_text(
            encoding="utf-8"
        )
    )

    assert len(manifest["sources"]) == 1

    source = manifest["sources"][0]

    assert source["url"] == url
    assert source["final_url"] == url
    assert source["content_type"] == "text/markdown"
    assert source["size"] == len(content)
    assert source["sha256"]


def test_refresh_updates_existing_source(
    isolated_environment,
    monkeypatch,
):
    contents = [
        b"# Version 1",
        b"# Version 2",
    ]

    current = {"index": 0}

    def fake_download(url):
        response = FakeResponse(
            contents[current["index"]],
            content_type="text/markdown",
        )

        return response, url

    monkeypatch.setattr(
        ingestion,
        "_download",
        fake_download,
    )

    class FakeIndex:
        def ensure_current(self):
            pass

    monkeypatch.setattr(
        ingestion,
        "KnowledgeIndex",
        FakeIndex,
        raising=False,
    )

    url = "https://example.com/test.md"

    ingestion.add_knowledge_source(url)

    current["index"] = 1

    result = ingestion.refresh_knowledge_source(
        url
    )

    assert "Successfully ingested" in result

    manifest = json.loads(
        isolated_environment[2].read_text(
            encoding="utf-8"
        )
    )

    assert len(manifest["sources"]) == 1

    source_file = (
        isolated_environment[0]
        / manifest["sources"][0]["path"]
    )

    assert source_file.read_text(
        encoding="utf-8"
    ) == "# Version 2"


def test_remove_source(
    isolated_environment,
    monkeypatch,
):
    content = b"# Test"

    response = FakeResponse(
        content,
        content_type="text/markdown",
    )

    monkeypatch.setattr(
        ingestion,
        "_download",
        lambda url: (
            response,
            url,
        ),
    )

    class FakeIndex:
        def ensure_current(self):
            pass

    monkeypatch.setattr(
        ingestion,
        "KnowledgeIndex",
        FakeIndex,
        raising=False,
    )

    url = "https://example.com/test.md"

    ingestion.add_knowledge_source(url)

    manifest = json.loads(
        isolated_environment[2].read_text(
            encoding="utf-8"
        )
    )

    source_path = (
        isolated_environment[0]
        / manifest["sources"][0]["path"]
    )

    assert source_path.exists()

    result = ingestion.remove_knowledge_source(
        url
    )

    assert "Successfully removed" in result
    assert not source_path.exists()

    manifest = json.loads(
        isolated_environment[2].read_text(
            encoding="utf-8"
        )
    )

    assert manifest["sources"] == []

def test_redirect_to_http_rejected(
    monkeypatch,
):
    class RedirectResponse(FakeResponse):
        def __init__(self):
            super().__init__(
                b"",
                status_code=302,
                headers={
                    "Location": "http://example.com/file.md"
                },
            )
            self.is_redirect = True

    monkeypatch.setattr(
        ingestion.requests,
        "get",
        lambda *args, **kwargs: RedirectResponse(),
    )

    with pytest.raises(ValueError, match="HTTPS"):
        ingestion._download(
            "https://example.com/file.md"
        )


def test_redirect_to_localhost_rejected(
    monkeypatch,
):
    class RedirectResponse(FakeResponse):
        def __init__(self):
            super().__init__(
                b"",
                status_code=302,
                headers={
                    "Location": "https://127.0.0.1/secret"
                },
            )
            self.is_redirect = True

    monkeypatch.setattr(
        ingestion.requests,
        "get",
        lambda *args, **kwargs: RedirectResponse(),
    )

    with pytest.raises(
        ValueError,
        match="Unsafe IP",
    ):
        ingestion._download(
            "https://example.com/file.md"
        )


def test_redirect_limit_enforced(
    monkeypatch,
):
    class RedirectResponse(FakeResponse):
        def __init__(self):
            super().__init__(
                b"",
                status_code=302,
                headers={
                    "Location": "https://example.com/again"
                },
            )
            self.is_redirect = True

    monkeypatch.setattr(
        ingestion.requests,
        "get",
        lambda *args, **kwargs: RedirectResponse(),
    )

    with pytest.raises(
        ValueError,
        match="Too many redirects",
    ):
        ingestion._download(
            "https://example.com/file.md"
        )


def test_download_size_limit_enforced(
    isolated_environment,
    monkeypatch,
):
    oversized = b"x" * (
        ingestion.MAX_DOWNLOAD_SIZE + 1
    )

    response = FakeResponse(
        oversized,
        content_type="text/markdown",
    )

    monkeypatch.setattr(
        ingestion,
        "_download",
        lambda url: (
            response,
            url,
        ),
    )

    result = ingestion.add_knowledge_source(
        "https://example.com/large.md"
    )

    assert "5 MB limit" in result
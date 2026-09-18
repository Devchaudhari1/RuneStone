import hashlib
import ipaddress
import json
import re
import socket
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests


PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXTERNAL_ROOT = PROJECT_ROOT / "knowledge" / "external"
MANIFEST_PATH = EXTERNAL_ROOT / "sources.json"

MAX_DOWNLOAD_SIZE = 5 * 1024 * 1024
REQUEST_TIMEOUT = 15
MAX_REDIRECTS = 5

ALLOWED_CONTENT_TYPES = {
    "text/plain",
    "text/markdown",
    "text/html",
}


def _load_manifest():
    if not MANIFEST_PATH.exists():
        return {"sources": []}

    with MANIFEST_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save_manifest(manifest):
    EXTERNAL_ROOT.mkdir(parents=True, exist_ok=True)

    with MANIFEST_PATH.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def _is_unsafe_ip(ip_string: str) -> bool:
    ip = ipaddress.ip_address(ip_string)

    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def _validate_hostname(hostname: str):
    if not hostname:
        raise ValueError("URL must contain a hostname.")

    hostname = hostname.rstrip(".")

    if hostname.lower() == "localhost":
        raise ValueError("Localhost URLs are not allowed.")

    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        ip = None

    if ip is not None:
        if _is_unsafe_ip(str(ip)):
            raise ValueError(
                f"Unsafe IP address is not allowed: {hostname}"
            )
        return

    try:
        addresses = socket.getaddrinfo(
            hostname,
            443,
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror as e:
        raise ValueError(
            f"Could not resolve hostname: {hostname}"
        ) from e

    for address in addresses:
        ip_string = address[4][0]

        if _is_unsafe_ip(ip_string):
            raise ValueError(
                f"Hostname resolves to an unsafe IP address: "
                f"{ip_string}"
            )


def _validate_url(url: str):
    parsed = urlparse(url)

    if parsed.scheme.lower() != "https":
        raise ValueError("Only HTTPS URLs are allowed.")

    if not parsed.netloc:
        raise ValueError("URL must contain a hostname.")

    if parsed.username or parsed.password:
        raise ValueError(
            "URLs containing username/password credentials are not allowed."
        )

    _validate_hostname(parsed.hostname)

    return parsed


def _safe_filename(url: str):
    parsed = urlparse(url)

    path = parsed.path.strip("/")

    if not path:
        path = "index"

    name = Path(path).name

    if not name:
        name = "index"

    name = re.sub(
        r"[^a-zA-Z0-9._-]",
        "_",
        name,
    )

    if "." not in name:
        name += ".txt"

    digest = hashlib.sha256(
        url.encode("utf-8")
    ).hexdigest()[:12]

    return f"{digest}_{name}"


def _html_to_text(html: str) -> str:
    html = re.sub(
        r"<script\b[^>]*>.*?</script>",
        "",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    html = re.sub(
        r"<style\b[^>]*>.*?</style>",
        "",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    html = re.sub(
        r"<[^>]+>",
        " ",
        html,
    )

    html = re.sub(
        r"\s+",
        " ",
        html,
    )

    return html.strip()


def _download(url: str):
    current_url = url

    for _ in range(MAX_REDIRECTS + 1):
        _validate_url(current_url)

        response = requests.get(
            current_url,
            timeout=REQUEST_TIMEOUT,
            stream=True,
            allow_redirects=False,
            headers={
                "User-Agent": "RuneStone-Knowledge-Ingestion/1.0"
            },
        )

        if response.is_redirect or response.is_permanent_redirect:
            location = response.headers.get("Location")

            response.close()

            if not location:
                raise ValueError(
                    "Redirect response did not provide a Location header."
                )

            from urllib.parse import urljoin

            current_url = urljoin(
                current_url,
                location,
            )

            continue

        response.raise_for_status()

        return response, current_url

    raise ValueError(
        f"Too many redirects. Maximum allowed: {MAX_REDIRECTS}."
    )


def _read_response(response):
    content_type = response.headers.get(
        "Content-Type",
        "",
    ).split(";")[0].strip().lower()

    if content_type not in ALLOWED_CONTENT_TYPES:
        response.close()

        return None, (
            f"Error: unsupported content type: "
            f"{content_type or '(unknown)'}"
        )

    content_length = response.headers.get(
        "Content-Length"
    )

    if content_length:
        try:
            declared_size = int(content_length)
        except ValueError:
            declared_size = None

        if (
            declared_size is not None
            and declared_size > MAX_DOWNLOAD_SIZE
        ):
            response.close()

            return None, (
                "Error: remote file exceeds "
                "the 5 MB limit."
            )

    chunks = []
    total_size = 0

    try:
        for chunk in response.iter_content(
            chunk_size=64 * 1024
        ):
            if not chunk:
                continue

            total_size += len(chunk)

            if total_size > MAX_DOWNLOAD_SIZE:
                return None, (
                    "Error: remote file exceeds "
                    "the 5 MB limit."
                )

            chunks.append(chunk)
    finally:
        response.close()

    raw = b"".join(chunks)

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None, (
            "Error: remote document is not valid UTF-8."
        )

    if content_type == "text/html":
        text = _html_to_text(text)

    return (
        {
            "raw": raw,
            "text": text,
            "content_type": content_type,
        },
        None,
    )


def _atomic_write(path: Path, text: str):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
    ) as temp:
        temp.write(text)
        temp_path = Path(temp.name)

    temp_path.replace(path)


def add_knowledge_source(url: str) -> str:
    """
    Download a remote HTTPS document and add it
    to knowledge/external/.
    """

    try:
        _validate_url(url)

        response, final_url = _download(url)

        data, error = _read_response(response)

        if error:
            return error

        raw = data["raw"]
        text = data["text"]
        content_type = data["content_type"]

        filename = _safe_filename(url)

        destination = EXTERNAL_ROOT / filename

        _atomic_write(
            destination,
            text,
        )

        sha256 = hashlib.sha256(raw).hexdigest()

        manifest = _load_manifest()

        sources = manifest.setdefault(
            "sources",
            [],
        )

        existing = next(
            (
                source
                for source in sources
                if source["url"] == url
            ),
            None,
        )

        record = {
            "url": url,
            "final_url": final_url,
            "path": str(
                destination.relative_to(PROJECT_ROOT)
            ),
            "content_type": content_type,
            "size": len(raw),
            "sha256": sha256,
            "last_updated": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        if existing:
            existing.update(record)
        else:
            sources.append(record)

        _save_manifest(manifest)

        # Refresh the persistent knowledge index.
        from tools.knowledge_index import KnowledgeIndex

        index = KnowledgeIndex()
        index.ensure_current()

        return (
            f"Successfully ingested {url}\n"
            f"Saved to: {record['path']}\n"
            f"Size: {len(raw)} bytes\n"
            f"SHA-256: {sha256}"
        )

    except requests.RequestException as e:
        return f"Error downloading knowledge source: {e}"

    except ValueError as e:
        return f"Error: {e}"

    except OSError as e:
        return f"Error writing knowledge source: {e}"


def refresh_knowledge_source(url: str) -> str:
    manifest = _load_manifest()

    source = next(
        (
            source
            for source in manifest.get("sources", [])
            if source["url"] == url
        ),
        None,
    )

    if source is None:
        return (
            f"Error: knowledge source is not registered: "
            f"{url}"
        )

    return add_knowledge_source(url)


def remove_knowledge_source(url: str) -> str:
    manifest = _load_manifest()

    sources = manifest.get(
        "sources",
        [],
    )

    source = next(
        (
            source
            for source in sources
            if source["url"] == url
        ),
        None,
    )

    if source is None:
        return (
            f"Error: knowledge source is not registered: "
            f"{url}"
        )

    path = PROJECT_ROOT / source["path"]

    try:
        if path.exists():
            path.unlink()

        manifest["sources"] = [
            item
            for item in sources
            if item["url"] != url
        ]

        _save_manifest(manifest)

        from tools.knowledge_index import KnowledgeIndex

        index = KnowledgeIndex()
        index.ensure_current()

        return f"Successfully removed {url}"

    except OSError as e:
        return f"Error removing knowledge source: {e}"
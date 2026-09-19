from __future__ import annotations

import os
from typing import Any

import requests


SEARXNG_URL = os.getenv(
    "SEARXNG_URL",
    "http://127.0.0.1:8888",
)

DEFAULT_MAX_RESULTS = 5
MAX_MAX_RESULTS = 10
REQUEST_TIMEOUT = 15


class WebSearchError(RuntimeError):
    """Raised when SearXNG cannot complete a search."""


def web_search(
    query: str,
    max_results: int = DEFAULT_MAX_RESULTS,
) -> str:
    """
    Search the web through the local SearXNG instance.

    This is intentionally the only web-search network path exposed
    to the RuneStone agent.
    """

    query = query.strip()

    if not query:
        return "Web search error: query cannot be empty."

    if len(query) > 1000:
        return "Web search error: query is too long."

    max_results = max(1, min(max_results, MAX_MAX_RESULTS))

    params = {
        "q": query,
        "format": "json",
        "categories": "general",
        "safesearch": 1,
    }

    try:
        response = requests.get(
            f"{SEARXNG_URL.rstrip('/')}/search",
            params=params,
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise WebSearchError(
            f"Could not connect to SearXNG at {SEARXNG_URL}: {exc}"
        ) from exc

    if response.status_code != 200:
        raise WebSearchError(
            f"SearXNG returned HTTP {response.status_code}: "
            f"{response.text[:500]}"
        )

    try:
        data: dict[str, Any] = response.json()
    except ValueError as exc:
        raise WebSearchError(
            "SearXNG returned invalid JSON."
        ) from exc

    results = data.get("results", [])

    if not results:
        return f"No web search results found for: {query}"

    lines = [
        f"Web search results for: {query}",
        "",
    ]

    for index, result in enumerate(results[:max_results], start=1):
        title = str(result.get("title") or "Untitled").strip()
        url = str(result.get("url") or "").strip()
        content = str(result.get("content") or "").strip()
        engine = result.get("engine") or ""

        lines.append(f"[{index}] {title}")

        if url:
            lines.append(f"URL: {url}")

        if content:
            lines.append(f"Snippet: {content}")

        if engine:
            lines.append(f"Source: {engine}")

        published = result.get("publishedDate")
        if published:
            lines.append(f"Published: {published}")

        lines.append("")

    return "\n".join(lines).strip()
from __future__ import annotations

from pathlib import Path

import requests


class DownloadError(RuntimeError):
    """Raised when a remote resource cannot be downloaded."""


def download_file(url: str, destination: Path, timeout_seconds: int = 60) -> Path:
    """Download a remote file to disk using streamed chunks."""
    destination.parent.mkdir(parents=True, exist_ok=True)

    try:
        with requests.get(url, stream=True, timeout=timeout_seconds) as response:
            response.raise_for_status()
            with destination.open("wb") as output_file:
                for chunk in response.iter_content(chunk_size=1024 * 64):
                    if chunk:
                        output_file.write(chunk)
    except requests.RequestException as exc:
        raise DownloadError(f"Failed to download {url}: {exc}") from exc

    return destination

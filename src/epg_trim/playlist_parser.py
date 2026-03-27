from __future__ import annotations

import re
from pathlib import Path

ATTRIBUTE_PATTERN = re.compile(r'(?P<name>[\w-]+)="(?P<value>[^"]*)"')
WHITESPACE_PATTERN = re.compile(r"\s+")


def normalize_identifier(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = WHITESPACE_PATTERN.sub(" ", value.strip().lower())
    return normalized or None


def _parse_extinf_identifier(extinf_line: str) -> str | None:
    attributes = {match.group("name").lower(): match.group("value") for match in ATTRIBUTE_PATTERN.finditer(extinf_line)}

    for key in ("tvg-id", "tvg-name"):
        candidate = normalize_identifier(attributes.get(key))
        if candidate:
            return candidate

    _, _, display_name = extinf_line.partition(",")
    return normalize_identifier(display_name)


def parse_playlist_identifiers(playlist_path: Path) -> set[str]:
    identifiers: set[str] = set()

    # Process playlist incrementally to keep memory usage stable for large files.
    with playlist_path.open("r", encoding="utf-8-sig", errors="replace") as playlist_file:
        for raw_line in playlist_file:
            line = raw_line.strip()
            if not line.startswith("#EXTINF"):
                continue

            identifier = _parse_extinf_identifier(line)
            if identifier:
                identifiers.add(identifier)

    return identifiers

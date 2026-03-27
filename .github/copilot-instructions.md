# Copilot Instructions

This repository implements the EPG-Trim service.

The goal of the service is to filter XMLTV EPG files by removing channels and programme entries that are not referenced in an IPTV playlist.

## Technology Stack

Language: Python 3.12+
Dependency management: uv
Packaging: pyproject.toml

## Distribution Artifacts

The project supports two distribution outputs:

1. Python package artifacts (wheel/sdist) via `uv build`
2. Self-contained executables via PyInstaller for deployment hosts

Executable artifacts are platform-specific and must be built on the target OS/architecture:

- Windows -> .exe
- Linux x64 -> ELF binary
- Raspberry Pi ARM -> ARM Linux binary

Do not assume a single binary can run on both Windows and Linux.

## Libraries

Use these libraries:

- requests  
- lxml  
- fastapi  
- uvicorn  
- apscheduler

Do not introduce additional dependencies unless necessary.

## XML Processing

EPG files can be very large.

XML must be processed using streaming parsing.

Use: lxml.etree.iterparse

Do not load the entire XML document into memory.

## Playlist Handling

Supported formats:

- M3U  
- M3U8

Channel identifiers must be extracted from `EXTINF` entries.

Priority order:

1. tvg-id
2. tvg-name
3. display name after comma

Example: `#EXTINF:0 tvg-rec="0",First Channel HD`

identifier = `First Channel HD`

Parse playlists line-by-line to avoid loading the full playlist into memory.

Identifiers must be normalized:

- trim whitespace
- convert to lowercase
- collapse multiple spaces

## Channel Matching

EPG channels must match playlist identifiers using:

1. channel@id
2. channel/display-name

Each <channel> may have multiple <display-name> elements.
Keep the channel if **any** display-name matches a playlist identifier.
Matching must be case-insensitive.

## EPG Cleaning

- Build a mapping: playlist identifier → channel id.
- Filter <programme> elements using this mapping.
- Use streaming parsing (lxml.iterparse) to avoid loading full XML into memory.

## HTTP Server

Use FastAPI.

Endpoints:

- /epg.xml  
- /epg.xml.gz

## Scheduler

Use APScheduler.

Default interval: 7200 seconds

## Project Modules

The project must contain the following modules:

- epg_trim/
  - downloader.py
  - playlist_parser.py
  - epg_cleaner.py
  - scheduler.py
  - server.py
  - main.py
# Product Specification

## Project Name

EPG-Trim

## Overview

EPG-Trim is a service that filters XMLTV EPG files by removing channels and programme entries that are not referenced in an IPTV playlist.

The service periodically downloads a playlist and an EPG file, performs filtering, and exposes a cleaned EPG via HTTP.

## Inputs

The service receives two URLs:

1. IPTV playlist
2. XMLTV EPG file

Supported playlist formats:

- M3U
- M3U8

Supported EPG formats:

- xml
- xml.gz

## Processing Workflow

1. Download playlist
2. Download EPG
3. Extract channel identifiers from playlist (tvg-id, tvg-name or display name)
4. Filter EPG channels
5. Filter programme entries
6. Generate cleaned XML
7. Generate gzipped output

## Update Interval

Default refresh interval: 7200 seconds (2 hours)

## Output

The service exposes:

- /epg.xml  
- /epg.xml.gz

Both contain only channels referenced in the playlist.

## Distribution Artifacts

The project produces two artifact types:

1. Python package artifacts (wheel/sdist)
2. Self-contained executable artifacts

Executable artifacts are platform-specific and include required runtime dependencies.

Required build targets:

- Windows executable (.exe)
- Linux x64 executable
- Raspberry Pi ARM Linux executable

Executable artifacts must be built on compatible target OS/architecture.

## Non Functional Requirements

- Low memory usage
- Streaming XML processing
- Fault tolerant updates
- Keep previous valid EPG if update fails

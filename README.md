# EPG-Trim

## Badges

[![CodeQL](https://github.com/liminal-loop/iptv-epg-trim/actions/workflows/codeql.yml/badge.svg)](https://github.com/liminal-loop/iptv-epg-trim/actions/workflows/codeql.yml)
[![Dev Build](https://github.com/liminal-loop/iptv-epg-trim/actions/workflows/dev-build.yml/badge.svg)](https://github.com/liminal-loop/iptv-epg-trim/actions/workflows/dev-build.yml)
[![Dependency License Audit](https://github.com/liminal-loop/iptv-epg-trim/actions/workflows/dependency-license-audit.yml/badge.svg)](https://github.com/liminal-loop/iptv-epg-trim/actions/workflows/dependency-license-audit.yml)
[![Dependabot](https://img.shields.io/badge/Dependabot-enabled-025E8C?logo=dependabot&logoColor=white)](https://github.com/liminal-loop/iptv-epg-trim/network/updates)

EPG-Trim is a lightweight service that reduces IPTV EPG (XMLTV) files by removing channels and programme entries that are not referenced in a given IPTV playlist.

The service periodically downloads an IPTV playlist and an XMLTV EPG file, filters unused channels, and exposes a cleaned EPG via HTTP.

The project is designed to run as a small self-hosted service with minimal memory usage using streaming XML processing.

## Features

- Supports IPTV playlists in **M3U and M3U8 format**
- Extracts channel identifiers from playlists using the following priority:
  1. `tvg-id` attribute
  2. `tvg-name` attribute
  3. Display name after the comma in EXTINF entries (important for playlists without tvg-id)
- Supports **XMLTV EPG files (.xml and .xml.gz)**
- Removes unused channels and programme entries
- Streaming XML processing for low memory usage
- Automatic refresh every 2 hours
- HTTP server exposing cleaned EPG

## HTTP Endpoints

- GET /epg.xml
- GET /epg.xml.gz
- GET /health

The EPG endpoints return only the channels referenced in the playlist.
The health endpoint returns service refresh state.

## Requirements

- Python 3.12+
- uv package manager

Install uv: https://github.com/astral-sh/uv

## Setup

```bash
uv sync
```

## Repository Policy

Contributions are welcome from any GitHub user.

Maintainer preference:

- When working locally in this repository, use the private maintainer identity (`liminal-loop`).

Project-specific local git config:

```bash
git config --global --replace-all 'includeIf."gitdir/i:C:/Users/khg1imb/SourceCode/__home__/iptv-epg-trim/".path' 'C:/Users/khg1imb/SourceCode/__home__/iptv-epg-trim/.gitconfig.project'
```

Tracked project config file:

- [.gitconfig.project](.gitconfig.project)

The file contains repository-specific values for:

- `user.name = liminal-loop`
- `user.email = dev@bytemania.eu`

## Run

```bash
uv run epg-trim
--playlist-url <PLAYLIST_URL>
--epg-url <EPG_URL>
```

## Build Python Package

```bash
uv build
```

This generates wheel/sdist package artifacts in `dist/`.

## Build Self-Contained Executable

`uv build` creates Python packages (wheel/sdist). If you need a standalone executable that already includes dependencies, use PyInstaller.

### Windows Build

```bash
uv run --with pyinstaller python scripts/build_executable.py --clean
```

Output:

- `dist/windows-amd64/epg-trim.exe` (machine/arch suffix depends on your host)

### Linux / Raspberry Pi Build

Build on the target architecture to ensure binary compatibility:

- x64 Linux: build on a Linux x64 host
- Raspberry Pi (ARM): build on Raspberry Pi OS (or compatible ARM Linux)

```bash
uv run --with pyinstaller python scripts/build_executable.py --clean
```

Output:

- `dist/linux-aarch64/epg-trim` or `dist/linux-armv7l/epg-trim` on Pi
- `dist/linux-x86_64/epg-trim` on x64 Linux

The generated executable is self-contained and includes required Python dependencies.
Build each target artifact on a compatible OS/architecture; one binary is not cross-platform.

## Dev Release Assets

On each successful push to `main`, CI publishes latest development binaries to the public GitHub release tag `dev-latest`.

Release assets:

- `epg-trim-dev-linux-x86_64`
- `epg-trim-dev-linux-armv7l`
- `epg-trim-dev-windows-amd64.exe`

These assets are publicly downloadable and do not require GitHub authentication.

## Use Executables

### Required Arguments

All executable variants require:

- `--playlist-url`
- `--epg-url`

Optional runtime arguments:

- `--interval-seconds` (default: `7200`)
- `--work-dir` (default: `data`)
- `--host` (default: `0.0.0.0`)
- `--port` (default: `8000`)

### Run on Windows

```powershell
.\dist\windows-amd64\epg-trim.exe \
  --playlist-url "https://example.com/playlist.m3u" \
  --epg-url "https://example.com/epg.xml.gz"
```

### Run on Linux x64

```bash
./dist/linux-x86_64/epg-trim \
  --playlist-url "https://example.com/playlist.m3u" \
  --epg-url "https://example.com/epg.xml.gz"
```

### Run on Raspberry Pi (ARM)

```bash
./dist/linux-armv7l/epg-trim \
  --playlist-url "https://example.com/playlist.m3u" \
  --epg-url "https://example.com/epg.xml.gz"
```

Or (for 64-bit Pi):

```bash
./dist/linux-aarch64/epg-trim \
  --playlist-url "https://example.com/playlist.m3u" \
  --epg-url "https://example.com/epg.xml.gz"
```

### Verify Service

After startup, check:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/epg.xml`
- `http://127.0.0.1:8000/epg.xml.gz`

If using a custom port, replace `8000` accordingly.

## Install As Linux Service (No Token)

Use the helper script to download the latest dev binary from public release assets, create a systemd service, enable auto-start on boot, and start it now.

```bash
chmod +x scripts/install_latest_dev_service.sh
./scripts/install_latest_dev_service.sh \
  --playlist-url "https://example.com/playlist.m3u8" \
  --epg-url "https://example.com/epg.xml.gz"
```

Optional overrides:

- `--release-tag` to install from a different release tag (default `dev-latest`)
- `--host` to change bind address (default `0.0.0.0`)
- `--port` to change service port (default `8000`)

## License

MIT

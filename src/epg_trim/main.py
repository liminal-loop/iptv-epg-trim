from __future__ import annotations

import argparse
import logging
from pathlib import Path

import uvicorn

from epg_trim.scheduler import EPGRefreshService, start_scheduler
from epg_trim.server import create_app


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EPG-Trim service")
    parser.add_argument("--playlist-url", required=True, help="M3U or M3U8 playlist URL")
    parser.add_argument("--epg-url", required=True, help="XMLTV URL (.xml or .xml.gz)")
    parser.add_argument("--interval-seconds", type=int, default=7200, help="Refresh interval in seconds")
    parser.add_argument("--work-dir", type=Path, default=Path("data"), help="Working directory for downloaded and output files")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    parser.add_argument("--port", type=int, default=8000, help="Bind port")
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

    service = EPGRefreshService(
        playlist_url=args.playlist_url,
        epg_url=args.epg_url,
        work_dir=args.work_dir,
    )

    service.refresh()
    scheduler = start_scheduler(service, interval_seconds=args.interval_seconds)

    app = create_app(service, cache_max_age=args.interval_seconds)

    try:
        uvicorn.run(app, host=args.host, port=args.port)
    finally:
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    main()

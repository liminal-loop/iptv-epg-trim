from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from apscheduler.schedulers.background import BackgroundScheduler

from epg_trim.downloader import download_file
from epg_trim.epg_cleaner import clean_epg
from epg_trim.playlist_parser import parse_playlist_identifiers

LOGGER = logging.getLogger(__name__)


@dataclass
class EPGState:
    last_successful_update: datetime | None = None
    last_error: str | None = None


class EPGRefreshService:
    def __init__(self, playlist_url: str, epg_url: str, work_dir: Path) -> None:
        self.playlist_url = playlist_url
        self.epg_url = epg_url
        self.work_dir = work_dir

        self._lock = Lock()
        self.state = EPGState()

        self.playlist_path = self.work_dir / "playlist.m3u"
        self.epg_source_path = self.work_dir / "source_epg"
        self.output_xml_path = self.work_dir / "epg.cleaned.xml"
        self.output_gzip_path = self.work_dir / "epg.cleaned.xml.gz"

    def refresh(self) -> None:
        if not self._lock.acquire(blocking=False):
            LOGGER.info("Refresh already in progress; skipping overlapping run")
            return

        self.work_dir.mkdir(parents=True, exist_ok=True)

        playlist_tmp = self.work_dir / "playlist.tmp"
        epg_tmp = self.work_dir / "source_epg.tmp"
        xml_tmp = self.work_dir / "epg.cleaned.xml.tmp"
        gzip_tmp = self.work_dir / "epg.cleaned.xml.gz.tmp"

        try:
            LOGGER.info("playlist download started")
            download_file(self.playlist_url, playlist_tmp)
            LOGGER.info("playlist download finished")

            LOGGER.info("epg download started")
            download_file(self.epg_url, epg_tmp)
            LOGGER.info("epg download finished")

            identifiers = parse_playlist_identifiers(playlist_tmp)
            LOGGER.info("epg filtering start")
            _, _, stats = clean_epg(epg_tmp, identifiers, xml_tmp, gzip_tmp)
            LOGGER.info(
                "epg filtering finished channels_processed=%s channels_kept=%s programmes_processed=%s programmes_kept=%s",
                stats.channels_processed,
                stats.channels_kept,
                stats.programmes_processed,
                stats.programmes_kept,
            )

            playlist_tmp.replace(self.playlist_path)
            epg_tmp.replace(self.epg_source_path)
            xml_tmp.replace(self.output_xml_path)
            gzip_tmp.replace(self.output_gzip_path)

            self.state.last_successful_update = datetime.now(timezone.utc)
            self.state.last_error = None
            LOGGER.info("Refresh finished successfully")
        except Exception as exc:
            self.state.last_error = str(exc)
            LOGGER.exception("Refresh failed")
        finally:
            for temp_file in (playlist_tmp, epg_tmp, xml_tmp, gzip_tmp):
                if temp_file.exists():
                    temp_file.unlink(missing_ok=True)
            self._lock.release()


def start_scheduler(service: EPGRefreshService, interval_seconds: int) -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        service.refresh,
        trigger="interval",
        seconds=interval_seconds,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=interval_seconds,
    )
    scheduler.start()
    return scheduler

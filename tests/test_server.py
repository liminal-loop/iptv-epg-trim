from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from epg_trim.server import create_app


@dataclass
class _StubService:
    output_xml_path: Path
    output_gzip_path: Path
    state: object


@dataclass
class _State:
    last_error: str | None = None
    last_successful_update: datetime | None = None


def _asgi_get(app, path: str) -> tuple[int, dict[str, str], bytes]:
    status_code: int | None = None
    headers: dict[str, str] = {}
    body_chunks: list[bytes] = []

    async def receive() -> dict:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: dict) -> None:
        nonlocal status_code
        if message["type"] == "http.response.start":
            status_code = message["status"]
            headers.update({k.decode("latin-1").lower(): v.decode("latin-1") for k, v in message["headers"]})
        elif message["type"] == "http.response.body":
            body_chunks.append(message.get("body", b""))

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
    }

    asyncio.run(app(scope, receive, send))
    assert status_code is not None
    return status_code, headers, b"".join(body_chunks)


class ServerTests(unittest.TestCase):
    def test_root_returns_openapi_spec(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            app = create_app(_StubService(tmp_path / "missing.xml", tmp_path / "missing.xml.gz", _State()))

            status, _, body = _asgi_get(app, "/")
            payload = json.loads(body.decode("utf-8"))

            self.assertEqual(status, 200)
            self.assertEqual(payload.get("openapi"), "3.1.0")
            self.assertEqual(payload.get("info", {}).get("title"), "EPG-Trim")

    def test_epg_endpoints_return_files_with_cache_header(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            xml = tmp_path / "epg.cleaned.xml"
            gz = tmp_path / "epg.cleaned.xml.gz"

            xml.write_text("<tv></tv>", encoding="utf-8")
            gz.write_bytes(b"gzip-bytes")

            app = create_app(_StubService(xml, gz, _State()), cache_max_age=7200)

            xml_status, xml_headers, xml_body = _asgi_get(app, "/epg.xml")
            self.assertEqual(xml_status, 200)
            self.assertEqual(xml_headers.get("cache-control"), "max-age=7200")
            self.assertEqual(xml_body, b"<tv></tv>")

            gz_status, gz_headers, gz_body = _asgi_get(app, "/epg.xml.gz")
            self.assertEqual(gz_status, 200)
            self.assertEqual(gz_headers.get("cache-control"), "max-age=7200")
            self.assertEqual(gz_body, b"gzip-bytes")

    def test_epg_endpoints_return_404_when_missing(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            app = create_app(_StubService(tmp_path / "missing.xml", tmp_path / "missing.xml.gz", _State()))

            xml_status, _, _ = _asgi_get(app, "/epg.xml")
            gz_status, _, _ = _asgi_get(app, "/epg.xml.gz")

            self.assertEqual(xml_status, 404)
            self.assertEqual(gz_status, 404)

    def test_epg_endpoints_return_500_when_refresh_failed(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            app = create_app(
                _StubService(
                    tmp_path / "missing.xml",
                    tmp_path / "missing.xml.gz",
                    _State(last_error="download timeout"),
                )
            )

            xml_status, _, xml_body = _asgi_get(app, "/epg.xml")
            gz_status, _, gz_body = _asgi_get(app, "/epg.xml.gz")

            self.assertEqual(xml_status, 500)
            self.assertEqual(gz_status, 500)
            self.assertEqual(json.loads(xml_body.decode("utf-8"))["detail"], "EPG refresh failed")
            self.assertEqual(json.loads(gz_body.decode("utf-8"))["detail"], "EPG refresh failed")

    def test_health_endpoint_returns_starting_when_no_updates_yet(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            app = create_app(
                _StubService(
                    tmp_path / "missing.xml",
                    tmp_path / "missing.xml.gz",
                    _State(),
                )
            )

            status, _, body = _asgi_get(app, "/health")
            payload = json.loads(body.decode("utf-8"))

            self.assertEqual(status, 200)
            self.assertEqual(payload["status"], "starting")
            self.assertIsNone(payload["last_successful_update"])
            self.assertIsNone(payload["last_error"])

    def test_health_endpoint_returns_ok_after_successful_update(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            ts = datetime(2026, 3, 27, 12, 0, 0, tzinfo=timezone.utc)
            app = create_app(
                _StubService(
                    tmp_path / "epg.xml",
                    tmp_path / "epg.xml.gz",
                    _State(last_successful_update=ts),
                )
            )

            status, _, body = _asgi_get(app, "/health")
            payload = json.loads(body.decode("utf-8"))

            self.assertEqual(status, 200)
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["last_successful_update"], ts.isoformat())
            self.assertIsNone(payload["last_error"])

    def test_health_endpoint_returns_degraded_after_failure(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            app = create_app(
                _StubService(
                    tmp_path / "missing.xml",
                    tmp_path / "missing.xml.gz",
                    _State(last_error="network timeout"),
                )
            )

            status, _, body = _asgi_get(app, "/health")
            payload = json.loads(body.decode("utf-8"))

            self.assertEqual(status, 200)
            self.assertEqual(payload["status"], "degraded")
            self.assertIsNone(payload["last_successful_update"])
            self.assertEqual(payload["last_error"], "network timeout")


if __name__ == "__main__":
    unittest.main()
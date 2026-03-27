from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from epg_trim.scheduler import EPGRefreshService


def create_app(service: EPGRefreshService, cache_max_age: int = 7200) -> FastAPI:
    app = FastAPI(title="EPG-Trim")

    cache_header = {"Cache-Control": f"max-age={cache_max_age}"}

    @app.get("/")
    def get_openapi_spec() -> dict:
        return app.openapi()

    def _raise_if_unavailable(path_exists: bool) -> None:
        if path_exists:
            return
        if service.state.last_error:
            raise HTTPException(status_code=500, detail="EPG refresh failed")
        raise HTTPException(status_code=404, detail="EPG not available")

    @app.get("/epg.xml")
    def get_epg_xml() -> FileResponse:
        _raise_if_unavailable(service.output_xml_path.exists())

        return FileResponse(
            path=service.output_xml_path,
            media_type="application/xml",
            filename="epg.xml",
            headers=cache_header,
        )

    @app.get("/epg.xml.gz")
    def get_epg_gzip() -> FileResponse:
        _raise_if_unavailable(service.output_gzip_path.exists())

        return FileResponse(
            path=service.output_gzip_path,
            media_type="application/gzip",
            filename="epg.xml.gz",
            headers=cache_header,
        )

    @app.get("/health")
    def get_health() -> dict[str, str | None]:
        last_successful = service.state.last_successful_update
        if service.state.last_error:
            status = "degraded"
        elif last_successful is None:
            status = "starting"
        else:
            status = "ok"

        return {
            "status": status,
            "last_successful_update": last_successful.isoformat() if last_successful else None,
            "last_error": service.state.last_error,
        }

    return app

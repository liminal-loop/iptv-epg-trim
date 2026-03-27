# HTTP API Specification

## Endpoint

GET /epg.xml

Returns the cleaned XMLTV EPG.

## Endpoint

GET /epg.xml.gz

Returns the gzipped cleaned XMLTV EPG.

## Endpoint

GET /health

Returns current refresh health state.

Example response:

```json
{
	"status": "ok",
	"last_successful_update": "2026-03-27T12:00:00+00:00",
	"last_error": null
}
```

Status values:

- `starting`: no successful refresh yet
- `ok`: last refresh succeeded
- `degraded`: last refresh failed

## Response Codes

200 OK  
404 Not Found  
500 Internal Server Error

## Headers

Cache-Control: max-age=7200
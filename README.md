![ScanCan](https://github.com/bradsacks99/ScanCan/blob/main/scancan/static/scancan-logo.png)

# ScanCan

ScanCan is a containerized FastAPI service that exposes ClamAV scanning operations over HTTP.

## What It Provides

- Health endpoint for ClamAV status
- File path scanning
- URL content scanning
- Streaming upload scanning
- License endpoint
- OpenAPI docs at `/docs`

## Requirements

- Python 3.8-3.10
- Docker + Docker Compose (for container workflow)

## Project Layout

- `src/main.py`: FastAPI app and endpoints
- `src/clamav.py`: ClamAV client abstraction
- `src/models.py`: Pydantic models
- `src/logger.py`: logger wrapper
- `src/utils.py`: utility helpers
- `tests/`: pytest suite
- `docker-compose.yml`: local multi-container runtime
- `Makefile`: build, run, lint, type-check, and test commands

## Run With Docker Compose (Recommended)

Build images:

```bash
make build
```

Start services:

```bash
make up
```

Stop services:

```bash
make down
```

Restart with rebuild:

```bash
make restart
```

API will be available at:

- `http://localhost:8080`
- Docs: `http://localhost:8080/docs`

## Run Locally (Without Docker)

Create and sync environment with uv:

```bash
uv sync -p 3.9
source .venv/bin/activate
```

Start API:

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8080
```

Note: Local runtime still needs a reachable ClamAV daemon (socket or network) configured via environment variables below.

## Configuration

Configured in `src/config.py` via environment variables:

- `CLAMD_CONN`: `net` or `socket` (default: `net`)
- `CLAMD_HOST`: host for network mode (default: `lab3.local`)
- `CLAMD_PORT`: port for network mode (default: `3310`)
- `CLAMD_SOCKET`: socket path for socket mode (default: `/tmp/clamd.socket`)
- `UPLOAD_SIZE_LIMIT`: max upload/URL payload bytes (default: `104857600`)
- `USE_AUTHENTICATION`: `true`/`false` (default: `false`)
- `LOG_LEVEL`: logging level (default: `INFO`)
- `LOG_FORMAT`: logging format string

## Optional Addon Authentication Module

ScanCan supports a pluggable authentication module loaded from:

- `addon/authentication.py`

The path is hard-coded in the application and resolved relative to the current working directory.

The addon module must define this function:

```python
def authenticate(token: str):
	# Return True to allow, False to reject.
	# Any truthy non-False value is treated as allowed.
	return token == "my-secret-token"
```

Behavior:

- If `USE_AUTHENTICATION=false`, middleware auth is disabled.
- If `USE_AUTHENTICATION=true` and `addon/authentication.py` exists, ScanCan calls `authenticate(token)` from that module for protected requests.
- If the module is not present, ScanCan defaults to allow (request is treated as authenticated).
- If the module is present but does not expose a callable `authenticate(token)`, auth checks raise a runtime error.

To enable auth middleware:

```bash
export USE_AUTHENTICATION=true
```

## Testing and Quality Checks

Commands come from [Makefile](Makefile):

Run full checks (pylint + mypy + pytest):

```bash
make test
```

Run only pylint checks:

```bash
make pylint
```

Run only type checks:

```bash
make mypy
```

Run only tests:

```bash
make pytest
```

Run a single test module directly:

```bash
python -m pytest tests/test_main.py -v
```

## API Endpoints

- `GET /health`
- `POST /scanpath/{path}`
- `GET /scanurl/?url=...`
- `POST /contscan/{path}`
- `POST /scanfile`
- `GET /license`

See interactive docs at `http://localhost:8080/docs` for request/response schemas.

## Notes

- The previous benchmarking section has been removed.
- The README now reflects the current test suite and Makefile-driven workflow.

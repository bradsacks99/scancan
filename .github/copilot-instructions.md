# ScanCan Copilot Instructions

## Build, test, and lint commands

- **Environment setup:** `uv sync -p 3.9 && source .venv/bin/activate`
- **Important import-path requirement for local commands:** run Python tooling with `PYTHONPATH=src:.` from the repo root. `src/main.py` imports sibling modules with bare names like `import config` and `from clamav import ClamAv`, so local test and lint commands fail without that path setup.
- **Docker build/run workflow:** `make build`, `make up`, `make down`, `make restart`
- **Full local check suite:** `PYTHONPATH=src:. make test`
- **Tests only:** `PYTHONPATH=src:. make pytest`
- **Type checks:** `PYTHONPATH=src:. make mypy`
- **Lint:** `PYTHONPATH=src:. make pylint`
- **Run the whole pytest suite without activating the venv:** `PYTHONPATH=src:. uv run pytest tests/ -q`
- **Run one test module:** `PYTHONPATH=src:. python -m pytest tests/test_main.py -q`
- **Run one test function:** `PYTHONPATH=src:. python -m pytest tests/test_main.py::test_health -q`

## High-level architecture

- `src/main.py` is the service entrypoint and holds nearly all request orchestration: FastAPI app creation, optional auth middleware, custom exception types/handlers, and every HTTP endpoint.
- ClamAV access is funneled through `src/clamav.py`. The `ClamAv` wrapper owns the pyvalve client, re-establishes the connection on `PyvalveConnectionError` or missing client state, and exposes the small API that handlers call (`ping`, `version`, `stats`, `scan`, `contscan`, `instream`).
- Request handlers do not construct ClamAV clients directly. They depend on `clamav_init()` in `src/main.py`, which returns a singleton-style `ClamInstance`; keep new scan-related behavior behind that dependency instead of opening new pyvalve connections inside endpoints.
- Configuration is module-level in `src/config.py`, so environment variables are read at import time. Tests that need config changes monkeypatch `main_module.conf` or reload imported modules rather than calling a settings factory.
- Response payloads are built from Pydantic models in `src/models.py` and converted with `.model_dump()`. Scan failures should continue to flow through `ScanException` / `VirusFoundException` so the JSON shape stays consistent.
- Container and local execution paths are slightly different on purpose:
  - local/tests import `src.main`
  - the image copies `/src` into `/app`, sets `PYTHONPATH=/app`, and starts `uvicorn main:app`
  Keep that split in mind before changing import style or module paths.
- The Docker Compose stack is multi-container: `scancan` serves the API, `clam_base` provides the ClamAV daemon/runtime base, and `fresh_clam` refreshes virus definitions in the shared `clamdb` volume.

## Key conventions

- Keep Python changes compatible with **Python 3.9**. That is the version installed in `Dockerfile.scancan`, used in the README setup flow, and called out in `copilot_core_instructions.md`.
- Preserve the current bare-import style inside `src/` unless you also update the container entrypoint, `PYTHONPATH`, and test setup together. The current layout depends on it.
- The optional authentication hook is not a package or plugin system; it is a single file loaded from `addon/authentication.py` relative to the current working directory. When auth is enabled, the module must expose a callable `authenticate(token)`.
- Endpoint tests isolate behavior with FastAPI dependency overrides and monkeypatching instead of real network or ClamAV calls. Follow the existing `tests/test_main.py` pattern: override `clamav_init`, monkeypatch `aiohttp.ClientSession` or config values, and assert on HTTP responses.
- Health and scan success are determined by exact ClamAV response patterns, not just truthiness:
  - `/health` expects `PONG` and stats matching `^POOLS:.*\n\nSTATE:\sVALID\sPRIMARY\n`
  - virus detection is recognized from responses ending with or containing `FOUND`
- Logging goes through `src/logger.py`, which pulls `LOG_FORMAT` and `LOG_LEVEL` from `config` at import time and returns a standard `logging.Logger`.

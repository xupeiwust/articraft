# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

Articraft is an agentic system that generates articulated 3D objects (URDF models) from text prompts using LLMs (OpenAI, Gemini). It includes a custom geometry SDK, a generation agent with tool-use, a local storage/dataset layer, and a web-based 3D viewer.

## Common Commands

All commands use `just` (a command runner). Run `just` to list everything.

```bash
just setup                  # First-time setup (venv, deps, hooks, storage init)
just smoke-tests            # Run pytest suite
just format                 # ruff format
just lint                   # ruff check
just viewer                 # Start viewer (builds frontend, opens browser)
just viewer-dev             # Start viewer in dev mode (API + Vite HMR)
just viewer-api             # Start only the API server
just viewer-web-lint        # ESLint on viewer/web
just viewer-web-typecheck   # TypeScript type-check on viewer/web
just wb "prompt text"       # Generate an object from a prompt (workbench mode)
just wb-init "prompt text"  # Create a draft workbench record without running generation
just compile data/records/<id>  # Recompile a record's model.py → model.urdf
just rerun data/records/<id>    # Re-run generation for an existing record in-place
just search-index           # Rebuild the workbench search index
```

### Running a single test

```bash
uv run --group dev pytest tests/storage/test_repo.py -q
uv run --group dev pytest tests/sdk/test_imports.py::test_name -q
```

### Frontend only

```bash
npm --prefix viewer/web run dev         # Vite dev server
npm --prefix viewer/web run build       # Production build
npm --prefix viewer/web run lint        # ESLint
npm --prefix viewer/web run typecheck   # tsc
```

## Architecture

### Package layout

- **`agent/`** — Generation runtime. `runner.py` is the main entrypoint; `harness.py` contains `ArticraftAgent` which orchestrates the multi-turn LLM loop; `compiler.py` executes generated scripts and produces URDF; `providers/` has OpenAI and Gemini LLM adapters; `tools/` defines the tool-use registry; `prompts/` has system prompt templates; `tui/` has the terminal display.
- **`sdk/`** — The articulated-object SDK that generated code imports. `sdk/v0/` is the main implementation. Exports geometry primitives (Box, Cylinder, Sphere, etc.), boolean ops, spline helpers, loft/sweep/extrude, placement utilities, and validation (overlap/collision checking). Models are `ArticulatedObject` composed of `Part`s with `Articulation`s.
- **`sdk_hybrid/`** — Alternate SDK variant (same interface, different internals).
- **`storage/`** — On-disk data layer. `layout.py` defines the canonical `data/` directory structure; `repo.py` is `StorageRepo`; `records.py`, `collections.py`, `datasets.py`, `runs.py`, `manifests.py` handle CRUD. `search.py` manages a SQLite search index.
- **`viewer/`** — Local inspection tool. `viewer/api/` is a FastAPI app (`app.py`) served by uvicorn; `viewer/web/` is a React + TypeScript + Tailwind + Three.js SPA (Vite, shadcn/ui components).
- **`cli/`** — CLI entrypoints registered as `articraft-dataset` and `articraft-workbench` in pyproject.toml.
- **`tests/`** — pytest tests mirroring package structure. Smoke-level checks (imports, storage layout, API).

### Data flow

1. User prompt → `agent/runner.py` → `ArticraftAgent` (multi-turn LLM with tool-use) → generated `model.py` that uses `sdk`
2. `agent/compiler.py` executes `model.py` → exports URDF XML + mesh assets
3. Results persisted to `data/records/<record_id>/` (record.json, model.py, model.urdf, provenance.json, cost.json, traces/, assets/)
4. `viewer/api` serves records; `viewer/web` renders them with Three.js

### Storage layout (`data/`)

- `data/records/<record_id>/` — One directory per generated object
- `data/categories/` — Dataset category metadata and prompt batches
- `data/local/workbench.json` — Local workbench collection
- `data/cache/` — Manifests, run logs, search index (all regenerable)

### Viewer architecture

The API (`viewer/api/app.py`) is a FastAPI app that serves both the REST API and the built frontend (`viewer/web/dist/`). In dev mode, Vite runs on :5173 and proxies `/api` to the uvicorn backend on :8765.

## Code Style

- Python: `ruff` with line-length 100, target py311. Rules: E, F, I (ignoring E501). Use `from __future__ import annotations`, explicit type hints. 4-space indent.
- TypeScript/React: ESLint + TypeScript strict mode. `@` alias maps to `viewer/web/src/`. Tailwind CSS v4 via Vite plugin. shadcn/ui component library.
- Imports use `@` prefix in the viewer frontend (e.g., `@/components/...`).

## Pre-commit Hooks

Pre-commit runs on commit: forbidden path check, secret scanning, text hygiene (trailing whitespace/newlines), ruff format, ruff check, viewer lint, viewer typecheck. Smoke tests run on pre-push.

Files under `data/` are exempt from the trailing-newline requirement. Paths like `.env`, `data/cache/`, `data/local/`, generated URDFs, and asset dirs are blocked from commits.

## Environment

Provider keys go in `.env`: `OPENAI_API_KEY` for OpenAI, `GEMINI_API_KEYS` for Gemini. The `.env` file is gitignored.

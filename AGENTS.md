# AGENTS.md — Lumora

Generative video editor. AI produces editable layers on the same timeline you edit by hand.
FastAPI backend, Next.js frontend, Genblaze for AI generation, Backblaze B2 for storage.

## Setup

```bash
uv sync                     # install deps (Python 3.13, managed by uv)
uv run python main.py       # dev server on :8000
```

## Package manager

Use `uv` exclusively. Never `pip`. Add deps with `uv add <pkg>`.

## Run a test

Standalone scripts at the repo root, NOT pytest. Each has `if __name__ == "__main__": asyncio.run(test())`:
```bash
uv run python test_timeline.py   # timeline/track/layer CRUD — needs Postgres at DATABASE_URL + migrations applied
uv run python test_tier0.py      # AI tier0 with MockLLMClient (no network)
uv run python test_tier1.py
uv run python test_agentic.py
uv run python test.py
```

## Architecture (read `functions_architecture.md`)

Source of truth for all module boundaries and function signatures. Key invariants:

- **`Asset` dataclass is the universal currency.** Every media function accepts and returns `Asset`, never raw paths.
- **Hard module boundaries:**
  - `core/media/` — ffmpeg operations only. No DB, no AI calls.
  - `core/timeline/` — DB state only. No ffmpeg, no AI calls.
  - `core/renderer/` — orchestrates timeline + media. Reads timeline, calls media functions, returns final Asset.
  - `core/ai/` — calls into media/, timeline/, storage/, jobs/. Never touches DB or ffmpeg directly.
- **Effects:** one file per effect in `core/media/effects/`, dispatched via `registry.py`.
- **`adj.md` refinements to follow during implementation:**
  - Return typed Pydantic models, not `dict` from core functions.
  - Use typed param objects (`TextLayerParams`, `EffectParams`, etc.) instead of `params: dict`.
  - Renderer should accept a timeline object, not a timeline ID (keeps renderer DB-free).
  - Cache manager in `core/storage/cache.py` (`cachePathFor`, `writeCacheBytes`) — done; use it for B2 downloads.
  - `models/` directory is for domain models (`Project`, `Timeline`, `Track`, `Layer`, `Asset`, `GenerationJob`, `AgenticRun`), not DB ORM models.

## Build order

1. `core/timeline/` + `core/media/` + `core/renderer/` — manual editing with zero AI
2. `core/ai/tier0.py` — cheap, no credit risk
3. `core/ai/tier1.py` — basic Genblaze pipeline, asset in B2
4. `core/ai/agentic.py` — generate-evaluate-retry-store loop
5. `core/assets/search_assets` + UI polish

## Project structure

```
auth/ assets/ ai/ jobs/ exports/   # feature packages: routes/ + controllers/ + schemas.py (HTTP layer)
core/           # domain logic (no HTTP concerns)
  assets/       # asset lifecycle
  media/        # ffmpeg ops + effects/ + transitions/
  timeline/     # projects, tracks, layers (DB state)
  renderer/     # orchestrates timeline + media
  storage/      # B2 upload/download, staging, cache, manifests
  jobs/         # celery app, tasks, dispatcher, notifications
  ai/           # tier0 (LLM reasoning), tier1 (generation), agentic (loop), llmClient
  services/     # thin cross-module glue only
routes/         # root-level FastAPI routers (projects, tracks, layers)
controllers/    # request/response handling (projects, tracks, layers)
middlewares/    # requestId, errorHandler (+ auth/middlewares/ for JWT)
models/         # domain models (Pydantic): Project, Timeline, TimelineDetail, ...
utils/          # shared helpers
main.py         # FastAPI app entrypoint
```

## Conventions

- AI modules (`core/ai/`) are just callers — same interface as manual editing.
- `core/services/` does no new work — only sequences calls across other core modules.
- B2 bucket layout: `uploads/`, `staging/`, `generated-audio/`, `generated-image/`, `renders/`, `manifests/`.

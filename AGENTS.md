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

## Run single test / lint

No test suite or linter configured yet. When added, prefer:
```bash
uv run pytest tests/test_<name>.py -k <test_name>
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
  - Add a cache manager layer in `storage/` between download and local use.
  - `models/` directory is for domain models (`Project`, `Timeline`, `Track`, `Layer`, `Asset`, `GenerationJob`, `AgenticRun`), not DB ORM models.

## Build order

1. `core/timeline/` + `core/media/` + `core/renderer/` — manual editing with zero AI
2. `core/ai/tier0.py` — cheap, no credit risk
3. `core/ai/tier1.py` — basic Genblaze pipeline, asset in B2
4. `core/ai/agentic.py` — generate-evaluate-retry-store loop
5. `core/assets/search_assets` + UI polish

## Project structure

```
core/           # domain logic (no HTTP concerns)
  assets/       # asset lifecycle
  media/        # ffmpeg ops + effects/
  timeline/     # projects, tracks, layers (DB state)
  renderer/     # orchestrates timeline + media
  storage/      # B2 upload/download, staging, manifests
  jobs/         # async job orchestration
  ai/           # tier0 (LLM reasoning), tier1 (generation), agentic (loop)
  services/     # thin cross-module glue only
routes/         # FastAPI routers
controllers/    # request/response handling
middlewares/    # FastAPI middleware
models/         # domain models (Pydantic)
utils/          # shared helpers
main.py         # FastAPI app entrypoint
```

## Conventions

- AI modules (`core/ai/`) are just callers — same interface as manual editing.
- `core/services/` does no new work — only sequences calls across other core modules.
- B2 bucket layout: `uploads/`, `staging/`, `generated-audio/`, `generated-image/`, `renders/`, `manifests/`.

# Lumora

Generative video editor where AI never bakes pixels — it produces editable layers on the same timeline you edit by hand.

## Tech Stack

- **Backend:** FastAPI (Python 3.13)
- **Frontend:** Next.js
- **AI Generation:** Genblaze
- **Storage:** Backblaze B2

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Python 3.13+

## Quick Start

```bash
uv sync                        # install dependencies
uv run python main.py          # start dev server on :8000
```

## Project Structure

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

See [functions_architecture.md](functions_architecture.md) for detailed module boundaries and function signatures.

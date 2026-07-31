# Lumora — API Routes, Controllers & Middleware

Builds directly on `functions_architecture.md`. Every route below is a thin
controller: parse request → call one or more functions from `core/` →
serialize response. No business logic lives in route handlers.

---

## 1. Middleware stack (order matters — top runs first on request, last on response)

```
1. RequestIDMiddleware        — attach a request_id (for logs + WS correlation)
2. CORSMiddleware              — Next.js frontend origin
3. LoggingMiddleware            — structured request/response logs, timing
4. AuthMiddleware               — validate session/JWT, attach current_user
5. RateLimitMiddleware          — protect Tier 1 endpoints from credit abuse
6. ExceptionHandlerMiddleware   — catch domain exceptions -> consistent JSON error shape
7. ProjectOwnershipMiddleware   — (dependency, not global) verify current_user owns project_id on write routes
```

Notes:
- **RateLimitMiddleware** matters specifically because Tier 1 spends GMI Cloud
  credits — this is the enforcement point for the two-tier cost design in
  the doc, not just generic API hygiene.
- **ProjectOwnershipMiddleware** is better implemented as a FastAPI
  `Depends()` on routers that take `project_id`/`timeline_id`, rather than
  truly global middleware, since it needs the path param.
- Auth mechanism (JWT/session/OAuth) isn't specified in the architecture
  doc — flag this as a decision you still need to make; everything below
  assumes a `get_current_user` dependency exists.

---

## 2. Routers overview

```
routers/
├── projects.py       /api/projects
├── timelines.py       /api/projects/{project_id}/timeline
├── tracks.py          /api/timelines/{timeline_id}/tracks
├── layers.py          /api/tracks/{track_id}/layers
├── assets.py          /api/assets
├── jobs.py            /api/jobs
├── ai.py              /api/ai   (tier0 + tier1 trigger endpoints)
├── exports.py         /api/exports
├── manifests.py       /api/assets/{asset_id}/manifest
└── ws.py              /ws/jobs/{job_id}
```

Each router file's handlers call into `services/`, `timeline/`, `renderer/`,
`storage/`, or `ai/` from the function architecture — never `media/`
directly (media/ has no notion of HTTP or project ownership).

---

## 3. Projects

| Method | Path | Controller calls |
|---|---|---|
| POST | `/api/projects/` | `timeline.projects.create_project` |
| GET | `/api/projects/{project_id}/timeline/` | `timeline.get_timeline` |
| PATCH | `/api/projects/{project_id}/timeline/` | `timeline.layers.update_layer` (bulk) |

---

## 4. Tracks & Layers

| Method | Path | Controller calls |
|---|---|---|
| POST | `/api/timelines/{timeline_id}/tracks/` | `timeline.tracks.add_track` |
| POST | `/api/tracks/{track_id}/layers/` | `timeline.layers.add_layer` (source="manual") |
| PATCH | `/api/layers/{layer_id}/` | `timeline.layers.update_layer` |
| DELETE | `/api/layers/{layer_id}/` | `timeline.layers.delete_layer` |

These are the routes the manual editor UI hits directly — trim, move,
retime a layer, etc. No AI involvement.

---

## 5. Assets

| Method | Path | Controller calls |
|---|---|---|
| POST | `/api/assets/import/` (multipart upload) | `assets.import_asset` → `storage.b2.upload_asset` |
| GET | `/api/assets/?q=&tags=` | `assets.search_assets` |
| PATCH | `/api/assets/{asset_id}/tags/` | `assets.tag_asset` |
| GET | `/api/assets/{asset_id}/manifest/` | `storage.manifest.get_manifest` |
| GET | `/api/assets/{asset_id}/url/` | `storage.b2.get_presigned_url` |

---

## 6. Jobs (async orchestration entrypoint)

| Method | Path | Controller calls |
|---|---|---|
| POST | `/api/jobs/` | `jobs.create_generation_job` → dispatches to Tier 0 or Tier 1 background task |
| GET | `/api/jobs/{job_id}/` | `jobs.get_job_status` |

`POST /api/jobs/` body: `{tier, job_type, prompt, project_id, ...}`. The
controller only creates the job row and enqueues the task — it does not run
generation inline. Actual work happens in the background task, which then
calls `jobs.notify_job_update` over the WS route as it progresses.

---

## 7. AI — Tier 0 (synchronous, free, no job needed)

Because Tier 0 is cheap LLM reasoning with no media generation, these can
be plain synchronous request/response routes rather than going through the
job queue at all — matches the doc's framing of Tier 0 as "free, returns
layer JSON only."

| Method | Path | Controller calls |
|---|---|---|
| POST | `/api/ai/captions/` | `ai.tier0.generate_captions` → returns TextLayer params |
| POST | `/api/ai/transitions/suggest/` | `ai.tier0.suggest_transition` |
| POST | `/api/ai/cuts/suggest/` | `ai.tier0.suggest_cut_points` |
| POST | `/api/ai/motion-spec/` | `ai.tier0.generate_motion_spec` |

Frontend pattern: call one of these, show the suggestion, and only on
user-accept does the frontend call the normal layer routes (§4) to commit
it — keeping "AI never touches the timeline directly" literal at the route
level too.

## 8. AI — Tier 1 (async, spends credits, goes through jobs + agentic loop)

| Method | Path | Controller calls |
|---|---|---|
| POST | `/api/ai/voiceover/` | `jobs.create_generation_job(tier=1)` → background task runs `ai.agentic.run_agentic_loop(ai.tier1.generate_voiceover, job)` |
| POST | `/api/ai/music/` | same, with `ai.tier1.generate_music` |
| POST | `/api/ai/image/` | same, with `ai.tier1.generate_image` |
| POST | `/api/jobs/{job_id}/accept/` | escalated job → `services.store_tier1_result` (user accepts best attempt) |
| POST | `/api/jobs/{job_id}/retry/` | escalated job → user manually retries → `ai.agentic.retry_with_next_provider` |

These routes never call `ai.tier1.*` directly — always through
`run_agentic_loop`, so evaluation/retry/escalation is never accidentally
bypassed by a route.

---

## 9. Exports / Rendering

| Method | Path | Controller calls |
|---|---|---|
| POST | `/api/exports/` | `renderer.render_timeline` → `storage.b2.upload_asset` (renders/) |
| GET | `/api/exports/{export_id}/` | status/poll, same shape as jobs |

Render is heavy — should itself go through `jobs/` as a job (tier could be
a third bucket, e.g. `tier="render"`) rather than blocking the request.

---

## 10. WebSocket

| Route | Purpose |
|---|---|
| `WS /ws/jobs/{job_id}/` | Streams `jobs.notify_job_update` payloads: job status changes, and — critically — each `AgenticRun` attempt as it happens (attempt 1 failed ASR, attempt 2 passed on provider B), so the provenance UI updates live instead of only showing the final result. |

---

## 11. Manifests / Provenance

| Method | Path | Controller calls |
|---|---|---|
| GET | `/api/assets/{asset_id}/manifest/` | `storage.manifest.get_manifest` |
| GET | `/api/jobs/{job_id}/attempts/` | list `AgenticRun` rows for a job (full attempt history, per doc §6) |

This last one isn't in your original endpoint table but is implied by "the
provenance UI" needing agentic attempt history to display — flagging it as
a small necessary addition, not scope creep, since the doc explicitly
describes this UI need in §6 and §9's rubric row.

---

## 12. Error shape (used by ExceptionHandlerMiddleware)

```json
{
  "error": {
    "code": "job_not_found | provider_unavailable | asset_not_found | ...",
    "message": "human readable",
    "request_id": "..."
  }
}
```

Domain exceptions (e.g. `AllProvidersFailedError` from the agentic loop)
should map to specific `code` values so the frontend can distinguish
"needs_review, show escalation UI" from a generic 500.

---

## Summary: request flow for a Tier 1 action (e.g. voiceover)

```
POST /api/ai/voiceover/
   ↓ AuthMiddleware, RateLimitMiddleware
routers/ai.py
   ↓
jobs.create_generation_job(tier=1)   # returns job_id immediately
   ↓ (background task)
ai.agentic.run_agentic_loop(ai.tier1.generate_voiceover, job)
   ↓ per attempt
   generate → storage.staging.move_to_staging → run_evaluation → decide
   ↓ pass                                 ↓ fail (retry) / fail (max) 
storage.staging.promote_staging_to_final   retry_with_next_provider / escalate
storage.manifest.write_manifest
timeline.layers.add_layer(source="genblaze_generated")
   ↓ throughout
jobs.notify_job_update → WS /ws/jobs/{job_id}/
```

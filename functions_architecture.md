# AI Studio Media App — Function Architecture (FastAPI rewrite)

Derived strictly from `architecture.md`. No features added or removed —
only reorganized using three accepted improvements:

1. `Asset` object instead of raw path strings, everywhere.
2. Hard module boundaries: `media/` (ffmpeg, no DB) ↔ `timeline/` (DB, no ffmpeg) ↔ `renderer/` (orchestrates the two).
3. Effects implemented as one-file-per-effect behind a small registry, instead of one giant `apply_effect()` if/elif.

The rule stays the same throughout: **the AI is just another caller of these
same functions.** Nothing in `ai/` touches the database or ffmpeg directly —
it only calls into `media/`, `timeline/`, `storage/`, and `jobs/`.

---

## Folder structure

```
core/
├── assets/
│   └── assets.py
├── media/
│   ├── video.py
│   ├── audio.py
│   ├── text.py
│   ├── subtitles.py
│   ├── image.py
│   ├── transitions.py
│   └── effects/
│       ├── registry.py
│       └── (blur.py, brightness.py, contrast.py, grayscale.py, ...)
├── timeline/
│   ├── projects.py
│   ├── tracks.py
│   └── layers.py
├── renderer/
│   └── renderer.py
├── storage/
│   ├── b2.py
│   ├── staging.py
│   └── manifest.py
├── jobs/
│   └── jobs.py
├── ai/
│   ├── tier0.py
│   ├── tier1.py
│   └── agentic.py
└── services/
    └── services.py   # thin cross-module glue only — see §9
```

---

## 0. The `Asset` type

Every media function accepts and returns `Asset`, never a raw path. This
matches the doc's own `Asset` model (`b2_key`, `sha256`, `manifest_ref`) and
means storage backend (local / B2 / cache) can change without touching
function signatures.

```python
@dataclass
class Asset:
    id: str
    source: Literal["upload", "ai"]
    mime_type: str
    duration: float | None
    b2_key: str | None
    local_path: str | None
    sha256: str | None
    manifest_ref: str | None
```

---

## 1. `assets/` — asset lifecycle

```python
def import_asset(local_path: str, project_id: str, kind: str) -> Asset
def get_media_info(asset: Asset) -> dict          # duration, fps, resolution, codec, has_audio
def search_assets(query: str, tags: list[str] = None) -> list[Asset]
def tag_asset(asset: Asset, tags: list[str]) -> Asset
```

---

## 2. `media/` — pure ffmpeg operations (no DB, no AI)

### video.py

```python
def separate_audio_video(asset: Asset) -> tuple[Asset, Asset]   # -> (video_only, audio_only)
def cut_video(asset: Asset, start: float, end: float) -> Asset
def concat_videos(assets: list[Asset]) -> Asset
```

### transitions.py

```python
def apply_transition(asset_a: Asset, asset_b: Asset, transition_type: str,
                      duration: float, easing: str) -> Asset
```

### text.py

```python
def add_text_overlay(asset: Asset, text: str, font: str, position: dict,
                      start_time: float, duration: float,
                      keyframes: dict | None = None) -> Asset
```

### subtitles.py

```python
def add_subtitles(asset: Asset, transcript_words: list[dict]) -> Asset
    # burns karaoke-style caption reveal from word timings (consumes Tier 0 output)
```

### audio.py

```python
def mix_audio_layer(video_asset: Asset, audio_asset: Asset,
                     volume_envelope: list[dict], start_time: float) -> Asset
```

### effects/registry.py

```python
def apply_effect(asset: Asset, filter_type: str, params: dict) -> Asset
    # looks up filter_type in the registry, dispatches to the matching
    # effects/<name>.py implementation. The branching isn't eliminated,
    # just relocated out of one giant function into a registry + isolated
    # per-effect files, matching EffectLayer(filter_type, params) 1:1.
```

### image.py

```python
def generate_thumbnail(asset: Asset, timestamp: float | None = None) -> Asset
    # backs the B2 event-notification trigger on renders/
```

---

## 3. `timeline/` — pure DB state (no ffmpeg, no AI)

### projects.py

```python
def create_project(name: str) -> dict
```

### tracks/timeline

```python
def create_timeline(project_id: str) -> dict
def add_track(timeline_id: str, kind: Literal["video", "audio", "text", "effects"]) -> dict
def get_timeline(timeline_id: str) -> dict
```

### layers.py

```python
def add_layer(track_id: str, layer_type: str, params: dict,
              source: Literal["manual", "llm_suggested", "genblaze_generated"]) -> dict
    # source is metadata only — same Layer shape regardless of who created it
def update_layer(layer_id: str, params: dict) -> dict
def delete_layer(layer_id: str) -> None
```

---

## 4. `renderer/` — orchestrates timeline + media

```python
def render_timeline(timeline_id: str) -> Asset
    # reads the timeline (timeline/), calls the matching media/ function
    # per layer (Clip/Text/Transition/Audio/Effect), returns final mp4 Asset.
    # This is the one function the "export" endpoint and the agentic
    # "store" step both ultimately call.
```

---

## 5. `storage/` — Backblaze B2

### b2.py

```python
def upload_asset(asset: Asset) -> str            # -> b2_key
def download_asset(b2_key: str) -> Asset
def get_presigned_url(b2_key: str, expires_in: int) -> str
```

### staging.py

```python
def move_to_staging(asset: Asset, run_id: str) -> Asset       # staging/{run_id}/
def promote_staging_to_final(asset: Asset, final_prefix: str) -> Asset
def delete_staging(run_id: str) -> None                       # backs the lifecycle TTL rule
```

### manifest.py

```python
def write_manifest(run_id: str, manifest: dict) -> str        # manifests/{run_id}.json, Object Lock
def get_manifest(asset_id: str) -> dict
```

B2 layout (unchanged from doc):

```
bucket/
 ├─ uploads/{project_id}/...
 ├─ staging/{run_id}/...
 ├─ generated-audio/{project_id}/...
 ├─ generated-image/{project_id}/...
 ├─ renders/{project_id}/{export_id}.mp4
 └─ manifests/{run_id}.json
```

---

## 6. `jobs/` — async orchestration

```python
def create_generation_job(project_id: str, tier: int, job_type: str, prompt: str) -> dict
def get_job_status(job_id: str) -> dict
def notify_job_update(job_id: str, payload: dict) -> None   # WS push
```

---

## 7. `ai/tier0.py` — LLM reasoning, free, layer-JSON only

Each of these **returns layer params and calls into `timeline/layers.py` /
`media/`** — it never writes media or DB rows itself.

```python
def generate_captions(transcript: str, word_timings: list[dict]) -> dict   # -> TextLayer params
def suggest_transition(clip_a_meta: dict, clip_b_meta: dict) -> dict       # type, duration, easing
def suggest_cut_points(timeline: dict, target_duration: float) -> list[dict]
def generate_motion_spec(style: str, layer_type: str) -> dict              # animation spec / keyframes
```

---

## 8. `ai/tier1.py` + `ai/agentic.py`

### tier1.py — real generation, spends credits

```python
def generate_voiceover(script: str, voice_config: dict, provider: str | None = None) -> Asset
def generate_music(prompt: str, duration: float, provider: str | None = None) -> Asset
def generate_image(prompt: str, provider: str | None = None) -> Asset
```

Each is a thin wrapper around a Genblaze `Pipeline.run()` with the provider
fallback chain — one function per media type, not one per provider.

### agentic.py — generate → evaluate → retry → store → escalate, capped at 3 attempts

```python
def evaluate_duration(script: str, candidate: Asset) -> bool
def evaluate_asr_roundtrip(script: str, candidate: Asset) -> float     # confidence score
def evaluate_silence_clipping(candidate: Asset) -> bool
def run_evaluation(candidate: Asset, expected: dict) -> dict           # -> AgenticRun.checks + score

def decide(agentic_run: dict) -> Literal["store", "retry", "escalate"]
def retry_with_next_provider(job: dict, failure_reason: str) -> Asset  # may rewrite prompt via LLM
def escalate(job: dict, best_attempt: dict) -> None                    # needs_review, human decides

def run_agentic_loop(generate_fn: Callable[..., Asset], job: dict,
                      max_attempts: int = 3) -> dict
    # orchestrates: generate_fn() -> run_evaluation() -> decide() -> loop/store/escalate
    # the ONE function tying tier1 generators + evaluators + storage together
```

---

## 9. `services/` — cross-module glue (organizational only, no new capability)

Thin functions that just sequence calls across the modules above so routes
and the AI agent don't duplicate multi-step wiring. Nothing here does new
work — each line calls a function already defined above.

```python
def import_and_layer(local_path: str, project_id: str, track_id: str, kind: str) -> dict
    # import_asset() -> add_layer(source="manual")

def store_tier1_result(job: dict, final_asset: Asset, track_id: str, layer_type: str) -> dict
    # promote_staging_to_final() -> write_manifest() -> add_layer(source="genblaze_generated")
```

---

## API surface (unchanged from doc, now backed by the above)

| Endpoint | Calls into |
|---|---|
| `POST /api/projects/` | `timeline/projects.py` |
| `GET/PATCH /api/projects/{id}/timeline/` | `timeline/` |
| `POST /api/jobs/` | `jobs/` → `ai/tier0.py` or `ai/tier1.py` + `ai/agentic.py` |
| `GET /api/jobs/{id}/` | `jobs/` |
| `WS /ws/jobs/{id}/` | `jobs/notify_job_update` |
| `GET /api/assets/?q=&tags=` | `assets/search_assets` |
| `GET /api/assets/{id}/manifest/` | `storage/manifest.py` |
| `POST /api/exports/` | `renderer/render_timeline` |

---

## Build order (unchanged from doc §10, now mapped to modules)

1. `timeline/` + `media/` + `renderer/` — manual editing works with zero AI.
2. `ai/tier0.py` — cheap, no credit risk.
3. `ai/tier1.py` without the loop yet — basic Genblaze pipeline, asset in B2.
4. `ai/agentic.py` wrapped around tier1 — the differentiator.
5. `assets/search_assets` + provenance UI polish — last, additive.

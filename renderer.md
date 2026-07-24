# Renderer Branch — Merge Notes

## Dependencies from other branches

- `core/media/video.py` — from `video` branch (includes cutVideo fix: input-level seeking)
- `core/media/transitions/` — from `transitions` branch
- `core/assets/` — from `assets` branch
- `models/asset.py` — from `assets` branch
- `core/timeline/` — from `timeline` branch
- `core/database.py` — from `timeline` branch

## New files (renderer-specific)

- `core/renderer/` — main render pipeline, asset resolver, ffmpeg graph builder
  - `renderer.py` — `renderTimeline(timeline, assetRegistry) -> Asset` (async entry, sync internals)
  - `assetResolver.py` — resolve `params["assetId"]` to Asset with local path
  - `ffmpegGraph.py` — build ffmpeg filter chains for text overlays, effects, audio mixing
- `core/media/audio.py` — `mixAudioLayer()` with volume, fadeIn/Out, startTime
- `core/media/text.py` — `addTextOverlay()` with drawtext filter
- `core/media/effects/` — registry + blur, brightness, contrast, grayscale
- `models/renderParams.py` — typed Pydantic params (ClipParams, TransitionParams, AudioParams, TextParams, EffectParams) + composition models (TimelineComposition, TrackComposition, LayerComposition)
- `test.py` — full test suite (unit + integration tests for render pipeline)

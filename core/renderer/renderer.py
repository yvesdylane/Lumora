from __future__ import annotations

import asyncio
from typing import Literal

from models.asset import Asset
from models.renderParams import (
    AudioParams,
    BlurParams,
    BrightnessParams,
    ClipParams,
    ContrastParams,
    EffectParams,
    GrayscaleParams,
    TextParams,
    TimelineComposition,
    TrackComposition,
    TransitionParams,
    EFFECT_PARAM_MAP,
)
from core.media.video import cutVideo, concatVideos
from core.media.transitions.registry import applyTransition
from core.renderer.assetResolver import resolveAsset, resolveAssetDuration
from core.renderer.ffmpegGraph import applyVideoFilters, mixAudioTracks


async def renderTimeline(
    timeline: TimelineComposition,
    assetRegistry: dict[str, Asset],
    outputFormat: Literal["mp4", "webm"] = "mp4",
) -> Asset:
    return await asyncio.get_event_loop().run_in_executor(
        None,
        _renderTimelineSync,
        timeline,
        assetRegistry,
        outputFormat,
    )


def _renderTimelineSync(
    timeline: TimelineComposition,
    assetRegistry: dict[str, Asset],
    outputFormat: str,
) -> Asset:
    tracks = sorted(timeline.tracks, key=lambda t: t.position)

    videoTracks = [t for t in tracks if t.kind == "video"]
    audioTracks = [t for t in tracks if t.kind == "audio"]
    textTracks = [t for t in tracks if t.kind == "text"]
    effectsTracks = [t for t in tracks if t.kind == "effects"]

    base = _processVideoTracks(videoTracks, assetRegistry)

    for textTrack in textTracks:
        textLayers = _parseTextLayers(textTrack.layers)
        if textLayers:
            base = applyVideoFilters(base, textLayers, [])

    for effectsTrack in effectsTracks:
        effectLayers = _parseEffectLayers(effectsTrack.layers)
        if effectLayers:
            base = applyVideoFilters(base, [], effectLayers)

    allAudio = []
    for audioTrack in audioTracks:
        audioLayers = _parseAudioLayers(audioTrack.layers)
        for params in audioLayers:
            audioAsset = resolveAsset(params.assetId, assetRegistry)
            allAudio.append((audioAsset, params))

    if allAudio:
        base = mixAudioTracks(base, allAudio)

    return base


def _processVideoTracks(
    videoTracks: list,
    assetRegistry: dict[str, Asset],
) -> Asset:
    if not videoTracks:
        raise ValueError("No video tracks found in timeline")

    allClips: list[Asset] = []

    for track in videoTracks:
        sortedLayers = sorted(track.layers, key=lambda l: l.position)
        clips, transitions = _splitClipAndTransitionLayers(sortedLayers)

        if not clips:
            continue

        processedClips = []
        for clipParams in clips:
            asset = resolveAsset(clipParams.assetId, assetRegistry)
            if clipParams.end is not None:
                cut = cutVideo(asset, clipParams.start, clipParams.end)
                processedClips.append(cut)
            elif clipParams.start > 0:
                duration = resolveAssetDuration(asset)
                cut = cutVideo(asset, clipParams.start, duration)
                processedClips.append(cut)
            else:
                processedClips.append(asset)

        transitionMap = _buildTransitionMap(transitions)

        merged = _mergeClipsWithTransitions(processedClips, transitionMap)
        allClips.append(merged)

    if len(allClips) == 1:
        return allClips[0]

    return concatVideos(allClips)


def _mergeClipsWithTransitions(
    clips: list[Asset],
    transitionMap: dict[int, TransitionParams],
) -> Asset:
    if len(clips) == 0:
        raise ValueError("No clips to merge")
    if len(clips) == 1:
        return clips[0]

    result = clips[0]
    for i in range(1, len(clips)):
        if i - 1 in transitionMap:
            params = transitionMap[i - 1]
            result = applyTransition(
                result,
                clips[i],
                params.type,
                params.duration,
                params.easing,
            )
        else:
            result = concatVideos([result, clips[i]])

    return result


def _splitClipAndTransitionLayers(layers: list) -> tuple[list[ClipParams], list[TransitionParams]]:
    clips = []
    transitions = []
    for layer in layers:
        if layer.layerType == "clip":
            clips.append(ClipParams(**layer.params))
        elif layer.layerType == "transition":
            transitions.append(TransitionParams(**layer.params))
    return clips, transitions


def _buildTransitionMap(transitions: list[TransitionParams]) -> dict[int, TransitionParams]:
    return {i: t for i, t in enumerate(transitions)}


def _parseAudioLayers(layers: list) -> list[AudioParams]:
    result = []
    for layer in layers:
        if layer.layerType == "audio":
            result.append(AudioParams(**layer.params))
    return result


def _parseTextLayers(layers: list) -> list[TextParams]:
    result = []
    for layer in layers:
        if layer.layerType == "text":
            result.append(TextParams(**layer.params))
    return result


def _parseEffectLayers(layers: list) -> list[EffectParams]:
    result = []
    for layer in layers:
        if layer.layerType == "effect":
            filterType = layer.params.get("filterType", "")
            paramClass = EFFECT_PARAM_MAP.get(filterType)
            if paramClass:
                result.append(paramClass(**layer.params))
    return result

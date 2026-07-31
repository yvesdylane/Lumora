from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Literal

from genblaze_core import BaseProvider, Pipeline, Modality, ModelSpec, ModelRegistry

from models.asset import Asset

logger = logging.getLogger(__name__)

DEFAULT_VOICEOVER_MODEL = "inworld-tts-1.5-mini"
DEFAULT_MUSIC_MODEL = "minimax-music-2.5"
DEFAULT_IMAGE_MODEL = "seedream-5.0-lite"
DEFAULT_VIDEO_MODEL = "pixverse-v6-t2v"


def _mapGenblazeAsset(
    gbAsset,
    source: Literal["upload", "ai"] = "ai",
) -> Asset:
    return Asset(
        id=gbAsset.asset_id,
        source=source,
        mimeType=gbAsset.media_type,
        duration=gbAsset.duration,
        localPath=gbAsset.url if gbAsset.url.startswith("/") else None,
        sha256=gbAsset.sha256,
    )


def _fixAudioVoiceId(voiceId: str) -> str:
    mapping = {
        "ashley": "Ashley",
        "ronald": "Ronald",
    }
    return mapping.get(voiceId.lower(), voiceId)


def _getAudioProvider(model: str | None = None, httpTimeout: float = 120.0) -> BaseProvider:
    from genblaze_gmicloud import GMICloudAudioProvider

    resolvedModel = model or DEFAULT_VOICEOVER_MODEL
    originalProvider = GMICloudAudioProvider(http_timeout=httpTimeout)
    originalSpec = originalProvider.models_default().get(resolvedModel)

    if originalSpec is None:
        return originalProvider

    isMusic = originalSpec.extras.get("is_music", False)

    if isMusic:
        fixedSpec = ModelSpec(
            model_id=originalSpec.model_id,
            modality=originalSpec.modality,
            param_aliases={"prompt": "lyrics"},
            param_allowlist=frozenset({
                "lyrics", "voice_id", "language", "seed", "duration",
                "duration_seconds", "negative_prompt", "reference_audio",
                "output_format", "tempo", "style_weight",
            }),
            param_constraints=originalSpec.param_constraints,
            param_defaults={},
            param_schemas=originalSpec.param_schemas,
            param_coercers=originalSpec.param_coercers,
            param_transformer=originalSpec.param_transformer,
            pricing=originalSpec.pricing,
            extras=originalSpec.extras,
        )
    else:
        fixedSpec = ModelSpec(
            model_id=originalSpec.model_id,
            modality=originalSpec.modality,
            param_aliases={"prompt": "text", "voice": "voice_id"},
            param_allowlist=frozenset({
                "text", "voice_id", "language", "seed", "duration",
                "negative_prompt", "reference_audio", "output_format",
            }),
            param_constraints=originalSpec.param_constraints,
            param_defaults={},
            param_schemas=originalSpec.param_schemas,
            param_coercers=originalSpec.param_coercers,
            param_transformer=originalSpec.param_transformer,
            pricing=originalSpec.pricing,
            extras=originalSpec.extras,
        )

    registry = ModelRegistry()
    registry.register(fixedSpec)
    return GMICloudAudioProvider(models=registry, http_timeout=httpTimeout)


def _getDefaultImageProvider() -> BaseProvider:
    from genblaze_gmicloud import GMICloudImageProvider
    return GMICloudImageProvider()


def _getDefaultVideoProvider() -> BaseProvider:
    from genblaze_gmicloud import GMICloudVideoProvider
    return GMICloudVideoProvider()


async def generateVoiceover(
    script: str,
    provider: BaseProvider | None = None,
    voiceConfig: dict | None = None,
    model: str | None = None,
) -> Asset:
    useModel = model or DEFAULT_VOICEOVER_MODEL
    if provider is None:
        provider = _getAudioProvider(useModel)
    voiceConfig = voiceConfig or {}

    voiceId = voiceConfig.get("voiceId", "Ashley")
    voiceId = _fixAudioVoiceId(voiceId)

    logger.info(f"generateVoiceover: provider={provider.name} model={useModel} voice={voiceId}")

    pipeline = Pipeline(name=f"voiceover-{uuid.uuid4().hex[:8]}")

    stepParams: dict = {"voice_id": voiceId}
    if "stability" in voiceConfig:
        stepParams["stability"] = voiceConfig["stability"]
    if "similarityBoost" in voiceConfig:
        stepParams["similarity_boost"] = voiceConfig["similarityBoost"]

    pipeline.step(
        provider,
        model=useModel,
        prompt=script,
        modality=Modality.AUDIO,
        params=stepParams,
    )

    result = await asyncio.to_thread(pipeline.run, fail_fast=True)
    succeeded = result.succeeded_steps()

    if not succeeded:
        raise RuntimeError(f"generateVoiceover failed: {result.error_summary}")

    gbAsset = succeeded[0].assets[0]
    asset = _mapGenblazeAsset(gbAsset)
    logger.info(f"generateVoiceover: done id={asset.id} duration={asset.duration}")
    return asset


async def generateMusic(
    prompt: str,
    provider: BaseProvider | None = None,
    duration: float = 30.0,
    model: str | None = None,
) -> Asset:
    useModel = model or DEFAULT_MUSIC_MODEL
    if provider is None:
        provider = _getAudioProvider(useModel, httpTimeout=300.0)

    logger.info(f"generateMusic: provider={provider.name} model={useModel} duration={duration}")

    pipeline = Pipeline(name=f"music-{uuid.uuid4().hex[:8]}")

    pipeline.step(
        provider,
        model=useModel,
        prompt=prompt,
        modality=Modality.AUDIO,
        params={"duration": duration},
    )

    result = await asyncio.to_thread(pipeline.run, fail_fast=True)
    succeeded = result.succeeded_steps()

    if not succeeded:
        raise RuntimeError(f"generateMusic failed: {result.error_summary}")

    gbAsset = succeeded[0].assets[0]
    asset = _mapGenblazeAsset(gbAsset)
    logger.info(f"generateMusic: done id={asset.id} duration={asset.duration}")
    return asset


async def generateImage(
    prompt: str,
    provider: BaseProvider | None = None,
    model: str | None = None,
    size: str | None = None,
) -> Asset:
    if provider is None:
        provider = _getDefaultImageProvider()
    model = model or DEFAULT_IMAGE_MODEL

    logger.info(f"generateImage: provider={provider.name} model={model} size={size}")

    pipeline = Pipeline(name=f"image-{uuid.uuid4().hex[:8]}")

    stepParams: dict = {}
    if size:
        stepParams["size"] = size

    pipeline.step(
        provider,
        model=model,
        prompt=prompt,
        modality=Modality.IMAGE,
        params=stepParams,
    )

    result = await asyncio.to_thread(pipeline.run, fail_fast=True)
    succeeded = result.succeeded_steps()

    if not succeeded:
        raise RuntimeError(f"generateImage failed: {result.error_summary}")

    gbAsset = succeeded[0].assets[0]
    asset = _mapGenblazeAsset(gbAsset)
    logger.info(f"generateImage: done id={asset.id}")
    return asset


async def generateVideo(
    prompt: str,
    provider: BaseProvider | None = None,
    model: str | None = None,
    duration: float = 5.0,
    aspectRatio: str = "16:9",
    quality: str = "720p",
) -> Asset:
    if provider is None:
        provider = _getDefaultVideoProvider()
    model = model or DEFAULT_VIDEO_MODEL

    logger.info(f"generateVideo: provider={provider.name} model={model} duration={duration}")

    pipeline = Pipeline(name=f"video-{uuid.uuid4().hex[:8]}")

    pipeline.step(
        provider,
        model=model,
        prompt=prompt,
        modality=Modality.VIDEO,
        params={
            "duration": int(duration),
            "aspect_ratio": aspectRatio,
            "quality": quality,
        },
    )

    result = await asyncio.to_thread(pipeline.run, fail_fast=True)
    succeeded = result.succeeded_steps()

    if not succeeded:
        raise RuntimeError(f"generateVideo failed: {result.error_summary}")

    gbAsset = succeeded[0].assets[0]
    asset = _mapGenblazeAsset(gbAsset)
    logger.info(f"generateVideo: done id={asset.id} duration={asset.duration}")
    return asset

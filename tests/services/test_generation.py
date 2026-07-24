from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.services.generation import (
    _buildJobArgs,
    _resultToLayer,
    generateAndApply,
    runAgenticGeneration,
)
from models.job import GenerationJob


class TestResultToLayer:
    def test_voiceover_returns_audio_layer(self):
        result = {"tier": 1, "jobType": "voiceover", "asset": {"id": "a1"}}
        layerType, params = _resultToLayer("voiceover", result)
        assert layerType == "audio"
        assert params["assetId"] == "a1"
        assert params["volume"] == 0.8

    def test_music_returns_audio_layer(self):
        result = {"tier": 1, "jobType": "music", "asset": {"id": "a2"}}
        layerType, params = _resultToLayer("music", result)
        assert layerType == "audio"
        assert params["assetId"] == "a2"

    def test_image_returns_clip_layer(self):
        result = {"tier": 1, "jobType": "image", "asset": {"id": "a3"}}
        layerType, params = _resultToLayer("image", result)
        assert layerType == "clip"
        assert params["assetId"] == "a3"

    def test_video_returns_clip_layer(self):
        result = {"tier": 1, "jobType": "video", "asset": {"id": "a4"}}
        layerType, params = _resultToLayer("video", result)
        assert layerType == "clip"
        assert params["assetId"] == "a4"

    def test_caption_returns_text_layer(self):
        result = {"tier": 0, "result": {"text": "Hello", "font": "Arial"}}
        layerType, params = _resultToLayer("caption", result)
        assert layerType == "text"
        assert params["text"] == "Hello"

    def test_transition_returns_transition_layer(self):
        result = {"tier": 0, "result": {"type": "fade", "duration": 1.0}}
        layerType, params = _resultToLayer("transition", result)
        assert layerType == "transition"
        assert params["type"] == "fade"

    def test_unknown_type_returns_none(self):
        layerType, params = _resultToLayer("unknown", {})
        assert layerType is None
        assert params == {}


class TestBuildJobArgs:
    def test_voiceover_with_json_payload(self):
        job = GenerationJob(
            id=str(uuid.uuid4()),
            projectId="proj-1",
            tier=1,
            jobType="voiceover",
            prompt=json.dumps({"script": "Hello", "voiceConfig": {"voiceId": "Ronald"}}),
            createdAt=datetime.now(timezone.utc),
            updatedAt=datetime.now(timezone.utc),
        )
        args = _buildJobArgs(job)
        assert args["script"] == "Hello"
        assert args["voiceConfig"] == {"voiceId": "Ronald"}

    def test_voiceover_with_plain_prompt(self):
        job = GenerationJob(
            id=str(uuid.uuid4()),
            projectId="proj-1",
            tier=1,
            jobType="voiceover",
            prompt="Just a script",
            createdAt=datetime.now(timezone.utc),
            updatedAt=datetime.now(timezone.utc),
        )
        args = _buildJobArgs(job)
        assert args["script"] == "Just a script"
        assert args["voiceConfig"] == {}

    def test_music_with_duration(self):
        job = GenerationJob(
            id=str(uuid.uuid4()),
            projectId="proj-1",
            tier=1,
            jobType="music",
            prompt=json.dumps({"duration": 60.0}),
            createdAt=datetime.now(timezone.utc),
            updatedAt=datetime.now(timezone.utc),
        )
        args = _buildJobArgs(job)
        assert args["duration"] == 60.0

    def test_image_with_model(self):
        job = GenerationJob(
            id=str(uuid.uuid4()),
            projectId="proj-1",
            tier=1,
            jobType="image",
            prompt=json.dumps({"model": "custom-model", "size": "1024x1024"}),
            createdAt=datetime.now(timezone.utc),
            updatedAt=datetime.now(timezone.utc),
        )
        args = _buildJobArgs(job)
        assert args["model"] == "custom-model"
        assert args["size"] == "1024x1024"

    def test_video_defaults(self):
        job = GenerationJob(
            id=str(uuid.uuid4()),
            projectId="proj-1",
            tier=1,
            jobType="video",
            prompt="A sunset",
            createdAt=datetime.now(timezone.utc),
            updatedAt=datetime.now(timezone.utc),
        )
        args = _buildJobArgs(job)
        assert args["prompt"] == "A sunset"
        assert args["duration"] == 5.0

    def test_invalid_json_prompt(self):
        job = GenerationJob(
            id=str(uuid.uuid4()),
            projectId="proj-1",
            tier=1,
            jobType="voiceover",
            prompt="not json {{{",
            createdAt=datetime.now(timezone.utc),
            updatedAt=datetime.now(timezone.utc),
        )
        args = _buildJobArgs(job)
        assert args["script"] == "not json {{{"
        assert args["voiceConfig"] == {}


@pytest.mark.asyncio
@patch("core.services.generation.addLayer", new_callable=AsyncMock)
@patch("core.services.generation.dispatchJob", new_callable=AsyncMock)
async def test_generateAndApply_on_success(
    mockDispatch,
    mockAddLayer,
    mockSession,
    fakeLayer,
):
    job = GenerationJob(
        id="job-1",
        projectId="proj-1",
        tier=1,
        jobType="voiceover",
        prompt="Hello",
        createdAt=datetime.now(timezone.utc),
        updatedAt=datetime.now(timezone.utc),
    )

    completed = MagicMock()
    completed.status = "completed"
    completed.result = {"tier": 1, "jobType": "voiceover", "asset": {"id": "a1"}}
    mockDispatch.return_value = completed
    mockAddLayer.return_value = fakeLayer

    result = await generateAndApply(mockSession, job, "track-1")

    mockDispatch.assert_called_once_with(mockSession, job)
    mockAddLayer.assert_called_once()
    assert result == fakeLayer


@pytest.mark.asyncio
@patch("core.services.generation.addLayer", new_callable=AsyncMock)
@patch("core.services.generation.dispatchJob", new_callable=AsyncMock)
async def test_generateAndApply_on_failure_returns_none(
    mockDispatch,
    mockAddLayer,
    mockSession,
):
    job = GenerationJob(
        id="job-2",
        projectId="proj-1",
        tier=1,
        jobType="voiceover",
        prompt="Hello",
        createdAt=datetime.now(timezone.utc),
        updatedAt=datetime.now(timezone.utc),
    )

    completed = MagicMock()
    completed.status = "failed"
    completed.result = None
    mockDispatch.return_value = completed

    result = await generateAndApply(mockSession, job, "track-1")

    assert result is None
    mockAddLayer.assert_not_called()


@pytest.mark.asyncio
@patch("core.services.generation.addLayer", new_callable=AsyncMock)
@patch("core.services.generation.runAgenticLoop", new_callable=AsyncMock)
async def test_runAgenticGeneration_stores_on_success(
    mockRunLoop,
    mockAddLayer,
    mockSession,
):
    from core.ai.agentic import AgenticResult, AgenticRun

    job = GenerationJob(
        id="job-3",
        projectId="proj-1",
        tier=1,
        jobType="voiceover",
        prompt="Hello",
        maxAttempts=3,
        createdAt=datetime.now(timezone.utc),
        updatedAt=datetime.now(timezone.utc),
    )

    mockAsset = MagicMock()
    mockAsset.id = "a1"

    mockResult = AgenticResult(
        asset=mockAsset,
        decision="store",
        attempts=1,
        runs=[AgenticRun(score=0.9, decision="store")],
    )
    mockRunLoop.return_value = mockResult

    result = await runAgenticGeneration(mockSession, job, "track-1")

    mockRunLoop.assert_called_once()
    mockAddLayer.assert_called_once()

    call_kwargs = mockAddLayer.call_args
    assert call_kwargs[1]["trackId"] == "track-1"
    assert call_kwargs[1]["layerType"] == "audio"
    assert call_kwargs[1]["source"] == "genblaze_generated"

    assert result.decision == "store"


@pytest.mark.asyncio
@patch("core.services.generation.addLayer", new_callable=AsyncMock)
@patch("core.services.generation.runAgenticLoop", new_callable=AsyncMock)
async def test_runAgenticGeneration_does_not_store_on_escalate(
    mockRunLoop,
    mockAddLayer,
    mockSession,
):
    from core.ai.agentic import AgenticResult, AgenticRun

    job = GenerationJob(
        id="job-4",
        projectId="proj-1",
        tier=1,
        jobType="music",
        prompt="A melody",
        maxAttempts=3,
        createdAt=datetime.now(timezone.utc),
        updatedAt=datetime.now(timezone.utc),
    )

    mockResult = AgenticResult(
        asset=None,
        decision="escalate",
        attempts=3,
        runs=[AgenticRun(score=0.2, decision="retry")],
    )
    mockRunLoop.return_value = mockResult

    result = await runAgenticGeneration(mockSession, job, "track-1")

    mockAddLayer.assert_not_called()
    assert result.decision == "escalate"

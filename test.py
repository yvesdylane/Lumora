from __future__ import annotations

import asyncio
import subprocess
import tempfile
import uuid
from pathlib import Path

from models.asset import Asset
from models.effect import EffectParams
from models.renderParams import (
    AudioParams,
    ClipParams,
    LayerComposition,
    TextParams,
    TimelineComposition,
    TrackComposition,
    TransitionParams,
)
from core.assets.assets import getMediaInfo
from core.renderer.renderer import renderTimeline
from core.media.video import cutVideo, concatVideos, separateAudioVideo
from core.media.audio import mixAudioLayer
from core.media.text import addTextOverlay
from core.media.effects.registry import applyEffect, getAvailableEffects
from core.media.transitions.registry import applyTransition, getAvailableTransitions

TEST_DIR = Path(tempfile.mkdtemp(prefix="lumora_test_"))


def _generateTestVideo(
    duration: float = 5.0,
    width: int = 640,
    height: int = 480,
    fps: int = 30,
    color: str = "blue",
) -> Asset:
    out = TEST_DIR / f"test_video_{uuid.uuid4().hex}.mp4"

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c={color}:s={width}x{height}:d={duration}:r={fps}",
            "-f", "lavfi",
            "-i", f"sine=frequency=440:duration={duration}",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-shortest",
            str(out),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    info = getMediaInfo(Asset(
        id="temp",
        source="upload",
        mimeType="video/mp4",
        localPath=str(out),
    ))

    return Asset(
        id=str(uuid.uuid4()),
        source="upload",
        mimeType="video/mp4",
        localPath=str(out),
        sha256=_sha256(out),
        duration=info.duration,
    )


def _generateTestAudio(duration: float = 5.0, freq: int = 440) -> Asset:
    out = TEST_DIR / f"test_audio_{uuid.uuid4().hex}.mp3"

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"sine=frequency={freq}:duration={duration}",
            "-c:a", "libmp3lame",
            str(out),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    return Asset(
        id=str(uuid.uuid4()),
        source="upload",
        mimeType="audio/mpeg",
        localPath=str(out),
        sha256=_sha256(out),
    )


def _sha256(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


async def testMediaFunctions():
    print("=" * 60)
    print("TEST: Media Functions (unit)")
    print("=" * 60)

    video1 = _generateTestVideo(duration=3.0, color="blue")
    video2 = _generateTestVideo(duration=3.0, color="red")
    print(f"Generated test videos: {video1.id[:8]}, {video2.id[:8]}")

    cut = cutVideo(video1, 0.5, 2.5)
    cutInfo = getMediaInfo(cut)
    print(f"cutVideo: {cutInfo.duration:.2f}s (expected ~2.0s)")

    merged = concatVideos([video1, video2])
    mergedInfo = getMediaInfo(merged)
    print(f"concatVideos: {mergedInfo.duration:.2f}s (expected ~6.0s)")

    videoOnly, audioOnly = separateAudioVideo(video1)
    print(f"separateAudioVideo: video={videoOnly.mimeType}, audio={audioOnly.mimeType}")

    cutForTrans = cutVideo(video1, 0.0, 2.5)
    cut2ForTrans = cutVideo(video2, 0.0, 2.5)
    transition = applyTransition(cutForTrans, cut2ForTrans, "fade", 1.0, "linear")
    transInfo = getMediaInfo(transition)
    print(f"applyTransition (fade): {transInfo.duration:.2f}s")

    audio1 = _generateTestAudio(duration=3.0, freq=440)
    audioMixed = mixAudioLayer(video1, audio1, volume=0.5, fadeIn=0.5)
    print(f"mixAudioLayer: OK (volume=0.5, fadeIn=0.5)")

    textAsset = addTextOverlay(
        video1, "Hello World", font="Arial", size=36, color="yellow",
        position={"x": 0.5, "y": 0.5}, startTime=0.0, duration=2.0,
    )
    print(f"addTextOverlay: OK")

    blurAsset = applyEffect(video1, "blur", EffectParams(effectType="blur", params={"sigma": 3}))
    print(f"applyEffect (blur): OK")

    brightnessAsset = applyEffect(video1, "brightness", EffectParams(effectType="brightness", params={"value": 0.2}))
    print(f"applyEffect (brightness): OK")

    contrastAsset = applyEffect(video1, "contrast", EffectParams(effectType="contrast", params={"value": 1.5}))
    print(f"applyEffect (contrast): OK")

    grayAsset = applyEffect(video1, "grayscale", EffectParams(effectType="grayscale"))
    print(f"applyEffect (grayscale): OK")

    print(f"\nAvailable transitions: {getAvailableTransitions()}")
    print(f"Available effects: {getAvailableEffects()}")
    print("✅ Media functions passed!\n")


async def testRenderPipeline():
    print("=" * 60)
    print("TEST: Render Pipeline (integration)")
    print("=" * 60)

    video1 = _generateTestVideo(duration=3.0, color="blue")
    video2 = _generateTestVideo(duration=3.0, color="red")
    audio1 = _generateTestAudio(duration=3.0, freq=440)

    assetRegistry = {a.id: a for a in [video1, video2, audio1]}
    print(f"Asset registry: {len(assetRegistry)} assets")

    timeline = TimelineComposition(
        tracks=[
            TrackComposition(
                kind="video",
                position=0,
                layers=[
                    LayerComposition(
                        layerType="clip",
                        params=ClipParams(assetId=video1.id, start=0.0, end=2.5).model_dump(),
                        position=0,
                    ),
                    LayerComposition(
                        layerType="transition",
                        params=TransitionParams(type="fade", duration=1.0).model_dump(),
                        position=1,
                    ),
                    LayerComposition(
                        layerType="clip",
                        params=ClipParams(assetId=video2.id, start=0.5).model_dump(),
                        position=2,
                    ),
                ],
            ),
            TrackComposition(
                kind="audio",
                position=1,
                layers=[
                    LayerComposition(
                        layerType="audio",
                        params=AudioParams(assetId=audio1.id, volume=0.6, fadeIn=0.5).model_dump(),
                        position=0,
                    ),
                ],
            ),
            TrackComposition(
                kind="text",
                position=2,
                layers=[
                    LayerComposition(
                        layerType="text",
                        params=TextParams(
                            text="Test Overlay",
                            size=24,
                            color="yellow",
                            position={"x": 0.5, "y": 0.1},
                            startTime=0.0,
                            duration=2.0,
                        ).model_dump(),
                        position=0,
                    ),
                ],
            ),
        ],
    )

    print(f"Timeline: {len(timeline.tracks)} tracks")
    for t in timeline.tracks:
        print(f"  - {t.kind} track (pos={t.position}): {len(t.layers)} layers")

    result = await renderTimeline(timeline, assetRegistry)
    resultInfo = getMediaInfo(result)

    print(f"\nRender result:")
    print(f"  ID: {result.id[:8]}")
    print(f"  Path: {result.localPath}")
    print(f"  Duration: {resultInfo.duration:.2f}s")
    print(f"  Resolution: {resultInfo.resolution}")
    print(f"  Codec: {resultInfo.codec}")
    print(f"  Has audio: {resultInfo.hasAudio}")

    assert result.localPath is not None, "Output path should not be None"
    assert Path(result.localPath).exists(), "Output file should exist"
    assert resultInfo.duration is not None, "Duration should not be None"
    assert resultInfo.duration > 0, "Duration should be positive"

    print("\n✅ Render pipeline passed!\n")


async def testRenderSingleClip():
    print("=" * 60)
    print("TEST: Render Single Clip (no transitions)")
    print("=" * 60)

    video1 = _generateTestVideo(duration=4.0, color="green")
    assetRegistry = {video1.id: video1}

    timeline = TimelineComposition(
        tracks=[
            TrackComposition(
                kind="video",
                position=0,
                layers=[
                    LayerComposition(
                        layerType="clip",
                        params=ClipParams(assetId=video1.id, start=1.0, end=3.0).model_dump(),
                        position=0,
                    ),
                ],
            ),
        ],
    )

    result = await renderTimeline(timeline, assetRegistry)
    resultInfo = getMediaInfo(result)
    print(f"Single clip render: {resultInfo.duration:.2f}s (expected ~2.0s)")

    assert resultInfo.duration is not None
    assert 1.0 <= resultInfo.duration <= 4.0, f"Expected ~2.0s, got {resultInfo.duration}s"

    print("✅ Single clip render passed!\n")


async def testRenderEffectsOnly():
    print("=" * 60)
    print("TEST: Render with Effects")
    print("=" * 60)

    video1 = _generateTestVideo(duration=3.0, color="yellow")
    assetRegistry = {video1.id: video1}

    from models.renderParams import EffectParams

    timeline = TimelineComposition(
        tracks=[
            TrackComposition(
                kind="video",
                position=0,
                layers=[
                    LayerComposition(
                        layerType="clip",
                        params=ClipParams(assetId=video1.id).model_dump(),
                        position=0,
                    ),
                ],
            ),
            TrackComposition(
                kind="effects",
                position=1,
                layers=[
                    LayerComposition(
                        layerType="effect",
                        params=EffectParams(filterType="blur").model_dump(),
                        position=0,
                    ),
                ],
            ),
        ],
    )

    result = await renderTimeline(timeline, assetRegistry)
    resultInfo = getMediaInfo(result)
    print(f"Effects render: {resultInfo.duration:.2f}s, resolution={resultInfo.resolution}")

    assert result.localPath is not None
    assert Path(result.localPath).exists()

    print("✅ Effects render passed!\n")


async def testTextParamsContentAlias():
    print("=" * 60)
    print("TEST: TextParams content alias")
    print("=" * 60)

    p = TextParams(content="Hello")
    assert p.text == "Hello", f"Expected text='Hello', got {p.text!r}"

    p2 = TextParams(text="Direct")
    assert p2.text == "Direct"

    p3 = TextParams(content="Aliased", size=32, rotation=10.0)
    assert p3.text == "Aliased"
    assert p3.size == 32
    assert p3.rotation == 10.0
    assert p3.opacity == 1.0
    assert p3.outlineWidth == 0
    assert p3.shadowX == 0.0
    assert p3.box is False
    assert p3.boxBorderW == 8

    p4 = TextParams(**{"text": "Legacy dict", "size": 20})
    assert p4.text == "Legacy dict"

    print("✅ TextParams content alias passed!\n")


async def testFontResolver():
    print("=" * 60)
    print("TEST: Font resolver")
    print("=" * 60)

    from core.renderer.fonts import resolveFontFile

    assert resolveFontFile(TextParams(font="Arial")) == \
        "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf"
    assert resolveFontFile(TextParams(fontFamily="Inter")) == \
        "/usr/share/fonts/rsms-inter-fonts/Inter-Regular.ttf"
    assert resolveFontFile(TextParams(fontFamily="Montserrat")) == \
        "/usr/share/fonts/julietaula-montserrat-fonts/Montserrat-Regular.otf"
    assert resolveFontFile(TextParams()) == \
        "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf"
    assert resolveFontFile(TextParams(fontFamily="NotARealFont")) == \
        "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf"

    print("✅ Font resolver passed!\n")


async def testTextFilterRichOptions():
    print("=" * 60)
    print("TEST: buildTextFilter rich options")
    print("=" * 60)

    from core.renderer.ffmpegGraph import buildTextFilter, buildFilterComplexGraph

    f = buildTextFilter(
        TextParams(
            content="Hi There",
            fontFamily="Inter",
            size=40,
            color="white",
            outlineWidth=2,
            outlineColor="red",
            shadowX=3,
            shadowY=4,
            shadowColor="black",
            box=True,
            boxColor="black",
            boxBorderW=6,
            opacity=0.5,
            position={"x": 0.5, "y": 0.9},
            startTime=0.0,
            duration=2.0,
        ),
        10.0,
    )
    assert "fontfile=/usr/share/fonts/rsms-inter-fonts/Inter-Regular.ttf" in f
    assert "fontsize=40" in f
    assert "fontcolor=white@0.5" in f
    assert "bordercolor=red:borderw=2" in f
    assert "shadowcolor=black:shadowx=3:shadowy=4" in f
    assert "box=1:boxcolor=black@0.5:boxborderw=6" in f
    assert "enable=between(t\\,0.0\\,2.0)" in f

    legacy = buildTextFilter(
        TextParams(text="Legacy", bgColor="black", size=20),
        5.0,
    )
    assert "box=1:boxcolor=black@0.6:boxborderw=8" in legacy

    inputs, graph = buildFilterComplexGraph(
        textLayers=[
            TextParams(content="Rot", rotation=15.0, position={"x": 0.1, "y": 0.9}),
            TextParams(content="Plain", position={"x": 0.5, "y": 0.5}),
        ],
        effectLayers=[],
        width=640,
        height=480,
        duration=2.0,
        fps=30,
    )
    assert len(inputs) == 8  # 2 layers x ("-f","lavfi","-i","color=...")
    assert "[0:v]null[base]" in graph
    assert graph.count("rotate=") == 1
    assert "fillcolor=0x00000000" in graph
    assert "format=rgba" in graph
    assert "overlay=x=-256:y=192:format=auto" in graph
    assert "[base][t0]overlay=" in graph

    print("✅ buildTextFilter rich options passed!\n")


async def main():
    print("\n" + "=" * 60)
    print("LUMORA RENDERER — FULL TEST SUITE")
    print("=" * 60 + "\n")

    await testMediaFunctions()
    await testRenderSingleClip()
    await testRenderEffectsOnly()
    await testTextParamsContentAlias()
    await testFontResolver()
    await testTextFilterRichOptions()
    await testRenderPipeline()

    print("=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

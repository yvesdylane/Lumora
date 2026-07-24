import asyncio

from dotenv import load_dotenv
load_dotenv()

from genblaze_core import MockAudioProvider, MockProvider

from core.ai.tier1 import generateVoiceover, generateMusic, generateImage, generateVideo


async def testGenerateVoiceoverMock():
    print("=" * 60)
    print("generateVoiceover (mock)")
    print("=" * 60)

    asset = await generateVoiceover(
        script="Hello, welcome to Lumora.",
        provider=MockAudioProvider(),
        model="mock-audio",
    )

    print(f"  id: {asset.id}")
    print(f"  mimeType: {asset.mimeType}")
    print(f"  source: {asset.source}")

    assert asset.source == "ai"
    assert asset.mimeType is not None
    print("  ✅ Passed")


async def testGenerateMusicMock():
    print("\n" + "=" * 60)
    print("generateMusic (mock)")
    print("=" * 60)

    asset = await generateMusic(
        prompt="Upbeat electronic music",
        provider=MockAudioProvider(),
        duration=10.0,
        model="mock-audio",
    )

    print(f"  id: {asset.id}")
    print(f"  mimeType: {asset.mimeType}")
    print(f"  source: {asset.source}")

    assert asset.source == "ai"
    assert asset.mimeType is not None
    print("  ✅ Passed")


async def testGenerateImageMock():
    print("\n" + "=" * 60)
    print("generateImage (mock)")
    print("=" * 60)

    asset = await generateImage(
        prompt="A small blue bird",
        provider=MockProvider(),
        model="mock-image",
    )

    print(f"  id: {asset.id}")
    print(f"  mimeType: {asset.mimeType}")
    print(f"  source: {asset.source}")

    assert asset.source == "ai"
    print("  ✅ Passed")


async def testGenerateImageReal():
    print("\n" + "=" * 60)
    print("generateImage (REAL — GMICloud Seedream)")
    print("=" * 60)

    asset = await generateImage(
        prompt="A golden retriever playing in autumn leaves, warm sunlight, cinematic",
    )

    print(f"  id: {asset.id}")
    print(f"  mimeType: {asset.mimeType}")
    print(f"  source: {asset.source}")
    print(f"  sha256: {asset.sha256}")

    assert asset.source == "ai"
    assert asset.mimeType is not None
    print("  ✅ Passed — real image generated!")


async def testGenerateVideoReal():
    print("\n" + "=" * 60)
    print("generateVideo (REAL — GMICloud PixVerse)")
    print("=" * 60)

    asset = await generateVideo(
        prompt="A cat walking through a sunlit garden, soft lighting",
    )

    print(f"  id: {asset.id}")
    print(f"  mimeType: {asset.mimeType}")
    print(f"  source: {asset.source}")
    print(f"  duration: {asset.duration}")
    print(f"  sha256: {asset.sha256}")

    assert asset.source == "ai"
    assert asset.mimeType is not None
    print("  ✅ Passed — real video generated!")


async def testGenerateVoiceoverReal():
    print("\n" + "=" * 60)
    print("generateVoiceover (REAL — GMICloud InWorld TTS)")
    print("=" * 60)

    asset = await generateVoiceover(
        script="Hello, this is a test of the Lumora AI video editor.",
    )

    print(f"  id: {asset.id}")
    print(f"  mimeType: {asset.mimeType}")
    print(f"  source: {asset.source}")
    print(f"  duration: {asset.duration}")
    print(f"  sha256: {asset.sha256}")

    assert asset.source == "ai"
    assert asset.mimeType is not None
    assert asset.id is not None
    print("  ✅ Passed — real voiceover generated!")


async def testGenerateMusicReal():
    print("\n" + "=" * 60)
    print("generateMusic (REAL — GMICloud MiniMax Music)")
    print("=" * 60)

    asset = await generateMusic(
        prompt="Upbeat electronic background music",
        duration=10.0,
    )

    print(f"  id: {asset.id}")
    print(f"  mimeType: {asset.mimeType}")
    print(f"  source: {asset.source}")
    print(f"  duration: {asset.duration}")
    print(f"  sha256: {asset.sha256}")

    assert asset.source == "ai"
    assert asset.mimeType is not None
    print("  ✅ Passed — real music generated!")


async def main():
    await testGenerateVoiceoverMock()
    await testGenerateMusicMock()
    await testGenerateImageMock()

    print("\n" + "~" * 60)
    print("Mock tests done. Now running REAL API tests...")
    print("~" * 60 + "\n")

    await testGenerateVoiceoverReal()
    await testGenerateMusicReal()
    await testGenerateImageReal()
    await testGenerateVideoReal()

    print("\n" + "=" * 60)
    print("✅ All tier1 tests passed (mock + real)!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

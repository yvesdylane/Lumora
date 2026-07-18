from core.media.transcribe import transcribeAudio
from core.media.subtitles import addSubtitles
from models.asset import Asset
from models.subtitle import SubtitleParams

video = Asset(
    id="demo",
    source="upload",
    mimeType="video/mp4",
    localPath="tests/media/fixtures/subtitle_sample.mp4",
)

print("Transcribing audio...")
words = transcribeAudio(video)
print(f"Found {len(words)} words")
for w in words[:10]:
    print(f"  {w.start:.2f}s - {w.end:.2f}s: {w.word}")
if len(words) > 10:
    print(f"  ... and {len(words) - 10} more")

print("\nBurning subtitles into video...")
params = SubtitleParams(
    words=words,
    fontSize=48,
    fontName="Arial",
    position="bottom",
    maxWordsPerLine=6,
)

result = addSubtitles(video, params)
print(f"\nOutput file: {result.localPath}")

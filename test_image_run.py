from pathlib import Path
from core.media.image import generateThumbnail, extractFrame, addImageOverlay
from models.asset import Asset

video = Asset(
    id="demo",
    source="upload",
    mimeType="video/mp4",
    localPath="tests/media/fixtures/sample.mp4",
)
image = Asset(
    id="logo",
    source="upload",
    mimeType="image/png",
    localPath="tests/media/fixtures/test_image.png",
)

print("=== 1. Generate Thumbnail ===")
thumb = generateThumbnail(video, timestamp=2.0)
print(f"Output: {thumb.localPath}")
print(f"MIME: {thumb.mimeType}")
print(f"Size: {Path(thumb.localPath).stat().st_size / 1024:.1f} KB")

print("\n=== 2. Extract Frame (PNG) ===")
frame_png = extractFrame(video, timestamp=2.0, format="png")
print(f"Output: {frame_png.localPath}")
print(f"MIME: {frame_png.mimeType}")
print(f"Size: {Path(frame_png.localPath).stat().st_size / 1024:.1f} KB")

print("\n=== 3. Extract Frame (JPG) ===")
frame_jpg = extractFrame(video, timestamp=4.0, format="jpg")
print(f"Output: {frame_jpg.localPath}")
print(f"MIME: {frame_jpg.mimeType}")
print(f"Size: {Path(frame_jpg.localPath).stat().st_size / 1024:.1f} KB")

print("\n=== 4. Add Image Overlay (centered, 3s) ===")
overlay = addImageOverlay(video, image, position={"x": "center", "y": "center"}, startTime=1.0, duration=3.0)
print(f"Output: {overlay.localPath}")
print(f"MIME: {overlay.mimeType}")
print(f"Size: {Path(overlay.localPath).stat().st_size / 1024 / 1024:.1f} MB")

print("\nAll tests completed!")

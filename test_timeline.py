import asyncio

from core.database import asyncSession
from core.timeline.projects import (
    createProject,
    deleteProject,
    getProject,
    listProjects,
    updateProject,
)
from core.timeline.timeline import createTimeline, deleteTimeline, getTimeline
from core.timeline.tracks import addTrack, deleteTrack, getTracks
from core.timeline.layers import addLayer, deleteLayer, getLayers, updateLayer

TEST_USER = "00000000-0000-0000-0000-000000000001"


async def test():
    async with asyncSession() as s:
        print("=" * 50)
        print("PROJECT")
        print("=" * 50)

        project = await createProject(s, "Test Project", TEST_USER)
        print(f"Created: {project.name} ({project.id})")

        got = await getProject(s, project.id)
        print(f"Got: {got.name}")

        updated = await updateProject(s, project.id, "Updated Project")
        print(f"Updated: {updated.name}")

        listed = await listProjects(s, TEST_USER)
        print(f"Listed: {len(listed)} project(s)")

        print("\n" + "=" * 50)
        print("TIMELINE")
        print("=" * 50)

        timeline = await createTimeline(s, project.id)
        print(f"Created timeline: {timeline.id}")

        gotTl = await getTimeline(s, timeline.id)
        print(f"Got timeline: {gotTl.id}")

        print("\n" + "=" * 50)
        print("TRACKS")
        print("=" * 50)

        track1 = await addTrack(s, timeline.id, "video")
        print(f"Added track: {track1.kind} (pos={track1.position})")

        track2 = await addTrack(s, timeline.id, "audio")
        print(f"Added track: {track2.kind} (pos={track2.position})")

        track3 = await addTrack(s, timeline.id, "text")
        print(f"Added track: {track3.kind} (pos={track3.position})")

        tracks = await getTracks(s, timeline.id)
        print(f"Tracks: {len(tracks)} total")

        print("\n" + "=" * 50)
        print("LAYERS")
        print("=" * 50)

        layer1 = await addLayer(
            s, track1.id, "clip",
            {"assetId": "abc-123", "start": 0, "end": 10},
            "manual",
        )
        print(f"Added layer: {layer1.layerType} source={layer1.source}")

        layer2 = await addLayer(
            s, track1.id, "transition",
            {"type": "fade", "duration": 2.0},
            "llm_suggested",
        )
        print(f"Added layer: {layer2.layerType} source={layer2.source}")

        layer3 = await addLayer(
            s, track2.id, "audio",
            {"volume": 0.8, "fadeIn": 1.0},
            "manual",
        )
        print(f"Added layer: {layer3.layerType} (pos={layer3.position})")

        layers = await getLayers(s, track1.id)
        print(f"Track 1 layers: {len(layers)} total")

        updatedLayer = await updateLayer(s, layer1.id, {"assetId": "abc-123", "start": 5, "end": 15})
        print(f"Updated layer params: {updatedLayer.params}")

        print("\n" + "=" * 50)
        print("CLEANUP (delete order: layers, tracks, timeline, project)")
        print("=" * 50)

        print(f"Delete layer: {await deleteLayer(s, layer1.id)}")
        print(f"Delete layer: {await deleteLayer(s, layer2.id)}")
        print(f"Delete layer: {await deleteLayer(s, layer3.id)}")
        print(f"Delete track: {await deleteTrack(s, track1.id)}")
        print(f"Delete track: {await deleteTrack(s, track2.id)}")
        print(f"Delete track: {await deleteTrack(s, track3.id)}")
        print(f"Delete timeline: {await deleteTimeline(s, timeline.id)}")
        print(f"Delete project: {await deleteProject(s, project.id)}")

        print("\n✅ All tests passed!")


if __name__ == "__main__":
    asyncio.run(test())

import asyncio
import json

from dotenv import load_dotenv
load_dotenv()

from core.database import asyncSession
from core.timeline.projects import createProject, deleteProject
from core.jobs.jobs import (
    createJob,
    getJob,
    listJobs,
    updateJobStatus,
    deleteJob,
)
from core.jobs.dispatcher import dispatchJob
from core.jobs.notifications import getConnections

TEST_USER = "00000000-0000-0000-0000-000000000001"


async def test():
    async with asyncSession() as s:
        print("=" * 60)
        print("PROJECT (setup)")
        print("=" * 60)

        project = await createProject(s, "Test Project", TEST_USER)
        print(f"Created project: {project.name} ({project.id})")

        print("\n" + "=" * 60)
        print("JOB CRUD")
        print("=" * 60)

        job = await createJob(
            s,
            project.id,
            tier=0,
            jobType="caption",
            prompt="Generate captions for the intro sequence",
        )
        print(f"Created job: {job.id[:8]} type={job.jobType} status={job.status}")
        assert job.status == "pending"
        assert job.tier == 0
        assert job.attempts == 0
        assert job.maxAttempts == 3

        got = await getJob(s, job.id)
        print(f"Got job: {got.id[:8]} prompt={got.prompt[:30]}...")
        assert got.id == job.id

        listed = await listJobs(s, project.id)
        print(f"Listed: {len(listed)} job(s)")
        assert len(listed) == 1

        print("\n" + "=" * 60)
        print("JOB STATUS UPDATES")
        print("=" * 60)

        running = await updateJobStatus(s, job.id, "running")
        print(f"Updated to: {running.status} attempts={running.attempts}")
        assert running.status == "running"
        assert running.attempts == 1

        completed = await updateJobStatus(
            s, job.id, "completed",
            result={"layerType": "text", "text": "Hello World"},
        )
        print(f"Updated to: {completed.status} result={completed.result}")
        assert completed.status == "completed"
        assert completed.result["text"] == "Hello World"

        print("\n" + "=" * 60)
        print("DISPATCHER — TIER 0 (caption)")
        print("=" * 60)

        captionPrompt = json.dumps({
            "transcript": "Welcome to Lumora, the AI video editor.",
            "wordTimings": [
                {"word": "Welcome", "start": 0.0, "end": 0.5},
                {"word": "to", "start": 0.5, "end": 0.7},
                {"word": "Lumora", "start": 0.7, "end": 1.2},
            ],
        })
        job3 = await createJob(
            s, project.id, tier=0, jobType="caption",
            prompt=captionPrompt,
        )

        dispatched = await dispatchJob(s, job3)
        print(f"Dispatched: status={dispatched.status}")
        assert dispatched.status == "completed"
        assert dispatched.result["tier"] == 0
        assert dispatched.result["jobType"] == "caption"

        print("\n" + "=" * 60)
        print("DISPATCHER — TIER 0 (transition)")
        print("=" * 60)

        transitionPrompt = json.dumps({
            "clipA": {"duration": 10.0, "type": "video"},
            "clipB": {"duration": 8.0, "type": "video"},
        })
        job4 = await createJob(
            s, project.id, tier=0, jobType="transition",
            prompt=transitionPrompt,
        )
        dispatched = await dispatchJob(s, job4)
        print(f"Dispatched: status={dispatched.status}")
        assert dispatched.status == "completed"
        assert dispatched.result["result"]["type"] in {
            "fade", "dissolve", "slideLeft", "wipeLeft",
            "wipeRight", "circleOpen", "fadeBlack",
        }

        print("\n" + "=" * 60)
        print("DISPATCHER — TIER 1 (voiceover — REAL)")
        print("=" * 60)

        voPrompt = json.dumps({"script": "Hello, welcome to Lumora."})
        job5 = await createJob(
            s, project.id, tier=1, jobType="voiceover",
            prompt=voPrompt,
        )
        dispatched = await dispatchJob(s, job5)
        print(f"Dispatched: status={dispatched.status}")
        assert dispatched.status == "completed"
        assert dispatched.result["asset"]["mimeType"].startswith("audio")

        print("\n" + "=" * 60)
        print("DISPATCHER — TIER 1 (music — REAL)")
        print("=" * 60)

        job6 = await createJob(
            s, project.id, tier=1, jobType="music",
            prompt="Upbeat electronic music for tech review",
        )
        dispatched = await dispatchJob(s, job6)
        print(f"Dispatched: status={dispatched.status}")
        assert dispatched.status == "completed"
        assert dispatched.result["asset"]["mimeType"].startswith("audio")

        print("\n" + "=" * 60)
        print("NOTIFICATIONS (in-memory WS)")
        print("=" * 60)

        conns = getConnections(job.id)
        print(f"Connections for job: {conns} (expected 0, no WS in test)")
        assert conns == 0

        print("\n" + "=" * 60)
        print("CLEANUP")
        print("=" * 60)

        for j in [job, job3, job4, job5, job6]:
            await deleteJob(s, j.id)
        await deleteProject(s, project.id)

        print("\n✅ All tests passed!")


if __name__ == "__main__":
    asyncio.run(test())

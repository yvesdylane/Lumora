Things I'd improve

These aren't criticisms—they're areas I'd refine before implementation.

1. Don't return dict everywhere

Right now you have:

def create_project(...) -> dict

def create_timeline(...) -> dict

def get_job(...) -> dict

In a FastAPI application, I'd strongly prefer returning typed domain models or Pydantic models.

For example:

def create_project(...) -> Project

def get_timeline(...) -> Timeline

def create_generation_job(...) -> GenerationJob

Only your API layer should convert those into JSON.

That gives you type safety, autocomplete, and clearer contracts.

2. params: dict is going to grow out of control

For example

add_layer(
    params={}
)

and

apply_effect(
    params={}
)

Today it's fine.

In six months it'll become

{
    "font":...
    "size":...
    "color":...
    "rotation":...
    ...
}

Instead I'd eventually introduce typed parameter objects:

TextLayerParams

TransitionParams

EffectParams

AudioLayerParams

You don't have to do this immediately, but I'd plan for it.

3. Timeline IDs in the renderer

This is the only design choice I'd probably change.

Right now

render_timeline(
    timeline_id
)

means the renderer has to fetch the timeline.

I would instead do:

timeline = get_timeline(id)

render_timeline(timeline)

Now the renderer knows nothing about your database.

That's a cleaner separation.

4. Storage responsibilities

Right now

storage/

↓

download_asset()

↓

Asset

I'd introduce a small cache manager.

Eventually you'll have logic like:

Need asset

↓

Already cached?

↓

yes

↓

use local

↓

no

↓

download from B2

↓

cache

↓

return Asset

That keeps storage concerns out of the media engine.

The one thing that's missing

If I had to add one module, it would be:

domain/

or

models/

Not database models—domain models.

Something like:

Project

Timeline

Track

Layer

Asset

GenerationJob

AgenticRun

Those become the shared language of the application.

Right now they're implied, but not explicitly represented in the architecture.

I would also tweak the build order slightly

Instead of:

timeline

media

renderer

I'd build:

Asset

↓

Media

↓

Timeline

↓

Renderer

↓

Storage

↓

Jobs

↓

Tier0

↓

Tier1

↓

Agentic

The reason is simple: the media layer is the foundation. Once you trust that it can cut, concatenate, overlay text, mix audio, and render correctly, everything else becomes orchestration around those primitives.

Overall verdict

I think this is a strong design document. It keeps the scope faithful to your original architecture, clearly separates concerns, and establishes a clean contract between manual editing and AI-assisted workflows. Most of my suggestions are about making the interfaces more strongly typed and preserving separation as the codebase grows, rather than changing the overall architecture.

If I were reviewing this as a lead engineer before implementation, I'd be comfortable approving it as the starting point for the FastAPI rewrite, with the expectation that typed models and parameter objects would be introduced as the implementation matures.

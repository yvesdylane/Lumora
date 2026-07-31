from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai.routes.ai import router as aiRouter
from assets.routes.assets import router as assetsRouter
from auth.routes.auth import router as authRouter
from jobs.routes.jobs import router as jobsRouter
from jobs.routes.ws import router as wsRouter
from middlewares.errorHandler import exceptionHandler
from middlewares.requestId import RequestIDMiddleware
from routes.layers import router as layersRouter
from routes.projects import router as projectsRouter
from routes.tracks import router as tracksRouter

app = FastAPI(title="Lumora", version="0.1.0")

app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(Exception, exceptionHandler)

app.include_router(authRouter)
app.include_router(assetsRouter)
app.include_router(projectsRouter)
app.include_router(tracksRouter)
app.include_router(layersRouter)
app.include_router(jobsRouter)
app.include_router(wsRouter)
app.include_router(aiRouter)


@app.get("/")
def hello_lumora():
    return {"message": "Hello Lumora"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

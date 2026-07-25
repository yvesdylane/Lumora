from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth.routes.auth import router as authRouter
from routes.projects import router as projectsRouter

app = FastAPI(title="Lumora", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(authRouter)
app.include_router(projectsRouter)


@app.get("/")
def hello_lumora():
    return {"message": "Hello Lumora"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

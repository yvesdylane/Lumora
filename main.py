from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from assets.routes.assets import router as assetsRouter
from auth.routes.auth import router as authRouter
from middlewares.errorHandler import exceptionHandler
from middlewares.requestId import RequestIDMiddleware

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


@app.get("/")
def hello_lumora():
    return {"message": "Hello Lumora"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

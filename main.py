from fastapi import FastAPI

app = FastAPI(title="Lumora", version="0.1.0")


@app.get("/")
def hello_lumora():
    return {"message": "Hello Lumora"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

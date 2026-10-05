from fastapi import FastAPI

app = FastAPI(title="EpitaCampus")


@app.get("/api/health")
def health():
    return {"status": "ok"}

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .db import Base, engine
from .icsync import sync_loop
from .routers import auth, calendar, courses, dashboard, grades

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Création des tables au démarrage (à remplacer par Alembic quand le schéma se stabilisera).
    Base.metadata.create_all(engine)
    task = asyncio.create_task(sync_loop())
    yield
    task.cancel()


app = FastAPI(title="EpitaCampus", lifespan=lifespan, docs_url="/api/docs", openapi_url="/api/openapi.json")

for router in (auth.router, courses.router, calendar.router, grades.router, dashboard.router):
    app.include_router(router)


@app.get("/api/health")
def health():
    return {"status": "ok"}

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import inspect, text

from .config import settings
from .db import Base, engine
from .icsync import sync_loop
from .moodle import sync_loop as moodle_sync_loop
from .routers import auth, calendar, courses, dashboard, grades, moodle

logging.basicConfig(level=logging.INFO)


def add_missing_columns() -> None:
    """Migration minimale : ajoute les nouvelles colonnes aux tables déjà existantes."""
    inspector = inspect(engine)
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if not inspector.has_table(table.name):
                continue
            existing = {c["name"] for c in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing:
                    continue
                col_type = column.type.compile(engine.dialect)
                ddl = f"ALTER TABLE {table.name} ADD COLUMN {column.name} {col_type}"
                if column.server_default is not None:
                    ddl += f" NOT NULL DEFAULT {column.server_default.arg}"
                conn.execute(text(ddl))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Création des tables au démarrage (à remplacer par Alembic quand le schéma se stabilisera).
    Base.metadata.create_all(engine)
    add_missing_columns()
    # Une synchro interrompue par un redémarrage ne doit pas rester bloquée.
    with engine.begin() as conn:
        conn.execute(text("UPDATE moodle_accounts SET syncing = false"))
    tasks = [asyncio.create_task(sync_loop()), asyncio.create_task(moodle_sync_loop())]
    yield
    for task in tasks:
        task.cancel()


# La documentation de l'API n'est exposée qu'en développement (SQLite).
dev = settings.database_url.startswith("sqlite")
app = FastAPI(
    title="EpitaCampus",
    lifespan=lifespan,
    docs_url="/api/docs" if dev else None,
    redoc_url=None,
    openapi_url="/api/openapi.json" if dev else None,
)

for router in (
    auth.router,
    courses.router,
    calendar.router,
    grades.router,
    dashboard.router,
    moodle.router,
):
    app.include_router(router)


@app.get("/api/health")
def health():
    return {"status": "ok"}

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings
from infrastructure.persistence.sqlalchemy.database import Database
from .endpoints import articles, search
from infrastructure.messaging.in_memory_event_bus import InMemoryEventBus


# main.py — lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    db = Database(
        url=settings.database_url,
    )

    if settings.is_dev:
        await db.init_db()

    event_bus = InMemoryEventBus()

    # ✅ Сохраняем в app.state для доступа через Depends
    app.state.settings = settings
    app.state.db = db
    app.state.event_bus = event_bus

    yield

    await db.close()


app = FastAPI(
    title="NewsMap API",
    description="API для визуализации новостей на карте",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware для инъекции DB session в request
@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    async with request.app.state.db.get_session() as session:
        request.state.db_session = session
        response = await call_next(request)
        return response


# Роуты
app.include_router(articles.router)
app.include_router(search.router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

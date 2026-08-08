import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import Base, engine
from app.routers import auth, tasks, users

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.validate_secrets()
    Base.metadata.create_all(bind=engine)
    logger.info("Database connection verified and tables ensured")
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Scratch Task Manager API", lifespan=lifespan)

    app.include_router(auth.router)
    app.include_router(tasks.router)
    app.include_router(users.router)

    @app.get("/", tags=["health"])
    def root():
        return {"message": "Woohoo!"}

    return app


app = create_app()
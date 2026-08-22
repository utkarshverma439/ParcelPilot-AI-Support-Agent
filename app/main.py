import os
import sys
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.data.models import init_db
from app.data.ingestion import run_ingestion
from app.vector.store import VectorStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("parcelpilot")

vector_store_instance = None
SessionLocal = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global vector_store_instance, SessionLocal

    settings = get_settings()
    logger.info(f"Starting ParcelPilot | model={settings.llm_model} db={settings.database_url[:30]}")

    db_url = settings.database_url
    if db_url.startswith("sqlite"):
        db_path = db_url.replace("sqlite:///", "")
        if not os.path.exists(db_path):
            SessionLocal = init_db(db_url)
            vector_store_instance = VectorStore()
            db = SessionLocal()
            try:
                run_ingestion(db, vector_store_instance)
            finally:
                db.close()
        else:
            SessionLocal = init_db(db_url)
            vector_store_instance = VectorStore()
    else:
        SessionLocal = init_db(db_url)
        vector_store_instance = VectorStore()
        db = SessionLocal()
        try:
            run_ingestion(db, vector_store_instance)
        finally:
            db.close()

    logger.info("ParcelPilot ready")
    yield
    logger.info("ParcelPilot shutting down")


app = FastAPI(
    title="ParcelPilot AI Support Agent",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.routes import router
app.include_router(router)

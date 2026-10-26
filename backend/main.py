
import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.routes import router
from backend.config import settings
from backend.database.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Qwen Agentic Web Assistant",
    version="0.1.0",
    description=(
        "Local-first Qwen assistant with a controlled custom agent loop."
    ),
    lifespan=lifespan,
)


@app.middleware("http")
async def require_api_key(request: Request, call_next):
    if request.url.path in ("/health", "/api/health"):
        return await call_next(request)

    expected_key = settings.qwen_agent_api_key

    if not expected_key:
        return JSONResponse(
            status_code=503,
            content={"detail": "API authentication is not configured."},
        )

    supplied_key = request.headers.get("X-API-Key", "")
    if not secrets.compare_digest(supplied_key, expected_key):
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid or missing API key."},
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return await call_next(request)


origins = [
    x.strip()
    for x in settings.cors_origins.split(",")
    if x.strip()
]

if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type", "X-API-Key"],
    )

app.include_router(router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok", "service": "qwen-agent-backend"}

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import router
from backend.database.db import init_db
from backend.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Qwen Agentic Web Assistant",version="0.1.0",
              description="Local-first Qwen assistant with a controlled custom agent loop.",lifespan=lifespan)
origins = [x.strip() for x in settings.cors_origins.split(",") if x.strip()]
if origins:
    app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=False,
                       allow_methods=["GET","POST","DELETE"],allow_headers=["Content-Type"])
app.include_router(router,prefix="/api")
@app.get("/health")
def health():
    return {"status":"ok","service":"qwen-agent-backend"}

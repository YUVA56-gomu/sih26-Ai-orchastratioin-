import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from config import CORS_ORIGINS
from session_store import SessionStore, init_db
from agents.orchestrator import Orchestrator
from routers.chat import router as chat_router
from routers.data import router as data_router
from routers.conversations import router as conversations_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("samudra")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    app.state.orca = Orchestrator(SessionStore())
    yield


app = FastAPI(
    title="ORCA Marine Intelligence API",
    version="2.0.0",
    description="Agentic marine decision-support backend with conversational AI, live ocean data, official hazard feeds, INCOIS enrichment, PFZ evidence, geofencing, route analysis and provenance.",
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Global safety net: the app must NEVER see a raw 500.

    Any unhandled exception is logged with its full traceback (so it stays
    debuggable) and translated into a valid, chat-friendly 200 response. The
    chat client reads `answer.summary`, so it shows a graceful message instead
    of a connection error on a 500.
    """
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=200,
        content={
            "error": str(exc),
            "answer": {
                "status": "info",
                "summary": "I couldn't complete that request just now. Please try again in a moment.",
                "observations": [],
                "recommendations": [],
            },
        },
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS != ["*"] else ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(data_router)
app.include_router(conversations_router)


@app.get("/")
def root():
    return {"name": "ORCA Marine Intelligence API", "version": "2.0.0", "docs": "/docs", "chat": "/api/chat", "websocket": "/api/chat/ws/{conversation_id}"}


@app.get("/health")
def health():
    return {"status": "ok"}

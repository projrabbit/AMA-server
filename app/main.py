import os
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router


load_dotenv()

PROJECT_NAME = os.getenv("PROJECT_NAME", "AMA Server")
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
DEBUG = os.getenv("DEBUG", "false").lower() in {"1", "true", "yes", "on"}
API_V1_PREFIX = os.getenv("API_V1_PREFIX", "/api/v1")
VERSION = os.getenv("VERSION", "0.1.0")


app = FastAPI(
    title=PROJECT_NAME,
    summary="Attendance Management API with indoor GIS support",
    description=(
        "AMA Server provides APIs for employee attendance, account access, trusted "
        "devices, shifts, fraud detection, audit logging, and indoor GIS/geofence data. "
        "Database objects are managed with Alembic in the business and gis schemas."
    ),
    version=VERSION,
    debug=DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=[
        {"name": "health", "description": "Application status and metadata endpoints."},
        {"name": "api", "description": "Versioned AMA API routes."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8080",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=API_V1_PREFIX, tags=["api"])


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail: Any = exc.detail
    if isinstance(detail, dict) and "code" in detail:
        error = {"code": detail["code"], "message": detail.get("message", ""), "details": detail.get("details", {})}
    else:
        error = {"code": "HTTP_ERROR", "message": str(detail), "details": {}}
    return JSONResponse(status_code=exc.status_code, content={"success": False, "error": error})


@app.get("/", tags=["health"])
def root() -> dict[str, str]:
    return {
        "name": PROJECT_NAME,
        "version": VERSION,
        "environment": ENVIRONMENT,
        "status": "running",
        "api_prefix": API_V1_PREFIX,
        "docs_url": "/docs",
    }


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": PROJECT_NAME,
        "version": VERSION,
        "environment": ENVIRONMENT,
    }

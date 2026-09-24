from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import admin, artwork, catalog, episodes, health, reference, shows
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title="Peblo TV Mini API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def readable_validation_errors(request: Request, exc: RequestValidationError):
    """
    Turn pydantic's nested error format into plain messages an editor can
    read directly (our field_validators already write full sentences --
    this just unwraps them instead of showing {"loc": [...], "msg": ...}).
    """
    messages = []
    for err in exc.errors():
        msg = err.get("msg", "Invalid value.")
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, "):]
        messages.append(msg)
    return JSONResponse(status_code=422, content={"detail": messages})


if settings.storage_backend == "local":
    import os
    os.makedirs(settings.storage_local_root, exist_ok=True)
    app.mount("/media", StaticFiles(directory=settings.storage_local_root), name="media")

app.include_router(health.router)
app.include_router(shows.router)
app.include_router(episodes.router)
app.include_router(artwork.router)
app.include_router(admin.router)
app.include_router(catalog.router)
app.include_router(reference.router)
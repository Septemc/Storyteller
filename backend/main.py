from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from .api import (
    routes_auth,
    routes_characters,
    routes_dungeon,
    routes_llm,
    routes_presets,
    routes_regex,
    routes_settings,
    routes_story,
    routes_templates,
    routes_worldbook,
)
from .db.crud.worldbook import cleanup_orphan_worldbook_embeddings
from .db.base import Base, engine
from .db.base import SessionLocal
from .scripts.migrate_worldbook_ids import run_migration


class DebugHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path.startswith("/api"):
            print(f"\n[REQUEST] {request.method} {request.url.path}")
            auth_header = request.headers.get("authorization", "None")
            preview = auth_header[:60] if auth_header != "None" else "None"
            print(f"[AUTH HEADER] {preview}...")

        response = await call_next(request)
        return response


app = FastAPI(title="Storyteller", version="0.2.0")

app.add_middleware(DebugHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    run_migration()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        cleanup_orphan_worldbook_embeddings(db)
    finally:
        db.close()


app.include_router(routes_story.router, prefix="/api", tags=["story"])
app.include_router(routes_worldbook.router, prefix="/api", tags=["worldbook"])
app.include_router(routes_characters.router, prefix="/api", tags=["characters"])
app.include_router(routes_dungeon.router, prefix="/api", tags=["dungeon"])
app.include_router(routes_settings.router, prefix="/api", tags=["settings"])
app.include_router(routes_presets.router, prefix="/api", tags=["presets"])
app.include_router(routes_llm.router, prefix="/api", tags=["llm"])
app.include_router(routes_regex.router, tags=["regex"])
app.include_router(routes_auth.router, tags=["auth"])
app.include_router(routes_templates.router)


BASE_DIR = Path(__file__).resolve().parents[1]
VUE_DIST_DIR = BASE_DIR / "frontend_vue" / "dist"
LEGACY_FRONTEND_DIR = BASE_DIR / "frontend"
FRONTEND_DIR = VUE_DIST_DIR if VUE_DIST_DIR.exists() else LEGACY_FRONTEND_DIR

if FRONTEND_DIR.exists():
    assets_dir = FRONTEND_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/", include_in_schema=False)
    async def serve_index() -> FileResponse:
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str) -> FileResponse:
        if full_path.startswith("api/") or full_path.startswith("regex/"):
            raise HTTPException(status_code=404, detail="Not Found")

        target = (FRONTEND_DIR / full_path).resolve()
        frontend_root = FRONTEND_DIR.resolve()
        if str(target).startswith(str(frontend_root)) and target.is_file():
            return FileResponse(target)

        html_target = (FRONTEND_DIR / f"{full_path}.html").resolve()
        if str(html_target).startswith(str(frontend_root)) and html_target.is_file():
            return FileResponse(html_target)

        return FileResponse(FRONTEND_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8010, reload=True)

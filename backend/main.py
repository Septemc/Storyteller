from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .db.base import Base, engine
from .api import (
    routes_story,
    routes_worldbook,
    routes_characters,
    routes_dungeon,
    routes_settings,
    routes_templates,
    # --- 本次重构新增 ---
    routes_presets,
    routes_llm,
)

app = FastAPI(title="Storyteller-说书人", version="0.2.0")

# 开发阶段先放开 CORS；如果你只用同一个域名访问，可以收紧策略
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    """启动时自动创建所有表。"""
    Base.metadata.create_all(bind=engine)


# 挂载各个路由模块，统一前缀 /api
app.include_router(routes_story.router, prefix="/api", tags=["story"])
app.include_router(routes_worldbook.router, prefix="/api", tags=["worldbook"])
app.include_router(routes_characters.router, prefix="/api", tags=["characters"])
app.include_router(routes_dungeon.router, prefix="/api", tags=["dungeon"])
app.include_router(routes_settings.router, prefix="/api", tags=["settings"])

# --- 本次重构核心：预设管理 / API 配置 ---
app.include_router(routes_presets.router, prefix="/api", tags=["presets"])
app.include_router(routes_llm.router, prefix="/api", tags=["llm"])

# 保持原有模板路由（如果为空也不会影响）
app.include_router(routes_templates.router)


# 前端静态资源与页面
BASE_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = BASE_DIR / "frontend"

if FRONTEND_DIR.exists():
    # 静态资源（CSS/JS）
    app.mount(
        "/assets",
        StaticFiles(directory=str(FRONTEND_DIR / "assets")),
        name="assets",
    )

    @app.get("/", include_in_schema=False)
    async def serve_index() -> FileResponse:
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/{page_name}.html", include_in_schema=False)
    async def serve_html_page(page_name: str) -> FileResponse:
        target = FRONTEND_DIR / f"{page_name}.html"
        if target.exists():
            return FileResponse(target)
        return FileResponse(FRONTEND_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8010, reload=True)

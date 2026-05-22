from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.core.config import settings

app = FastAPI(
    title="FleetOps API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(health_router)
app.include_router(auth_router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/docs", status_code=307)


@app.on_event("startup")
async def on_startup() -> None:
    print(f"FleetOps API starting in environment={settings.environment}")

import os

import pytest
from sqlalchemy import text

# Switch to local-host URL since tests run on host, not in container
# Note: postgres is mapped to port 5433 locally (5432 is in use by another service)
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://fleetops:fleetops_dev_password@localhost:5433/fleetops"
)

from app.core.database import engine, get_session  # noqa: E402


@pytest.mark.asyncio
async def test_engine_can_execute_select_one() -> None:
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1 AS value"))
        row = result.one()
        assert row.value == 1


@pytest.mark.asyncio
async def test_get_session_yields_async_session() -> None:
    gen = get_session()
    session = await gen.__anext__()
    try:
        result = await session.execute(text("SELECT 'hello' AS greeting"))
        assert result.scalar_one() == "hello"
    finally:
        await gen.aclose()

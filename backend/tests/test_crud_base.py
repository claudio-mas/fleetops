import uuid

import pytest
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.crud.base import CRUDBase
from app.models.base import Base, OperationalBase


class _Widget(OperationalBase):
    __tablename__ = "_widget_test"
    nome: Mapped[str] = mapped_column(String(255), nullable=False)


# Remove from app Base.metadata so conftest drop_all doesn't touch it.
Base.metadata.remove(_Widget.__table__)


widget_crud = CRUDBase(_Widget, search_fields=["nome"])

pytestmark = pytest.mark.anyio


@pytest.fixture(scope="session")
async def _widget_table(db_engine):  # type: ignore[no-untyped-def]
    async with db_engine.begin() as conn:
        await conn.run_sync(_Widget.__table__.create, checkfirst=True)
    yield
    async with db_engine.begin() as conn:
        await conn.run_sync(_Widget.__table__.drop, checkfirst=True)


async def test_create_then_get(db, _widget_table):
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    obj = await widget_crud.create(db, tenant_id=tid, user_id=uid, data={"nome": "Alpha"})
    await db.commit()
    fetched = await widget_crud.get(db, tenant_id=tid, obj_id=obj.id)
    assert fetched is not None
    assert fetched.nome == "Alpha"
    assert fetched.created_by == uid


async def test_get_other_tenant_returns_none(db, _widget_table):
    obj = await widget_crud.create(
        db, tenant_id=uuid.uuid4(), user_id=uuid.uuid4(), data={"nome": "X"}
    )
    await db.commit()
    assert await widget_crud.get(db, tenant_id=uuid.uuid4(), obj_id=obj.id) is None


async def test_list_filters_by_search_and_excludes_soft_deleted(db, _widget_table):
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    a = await widget_crud.create(db, tenant_id=tid, user_id=uid, data={"nome": "Bomba Diesel"})
    await widget_crud.create(db, tenant_id=tid, user_id=uid, data={"nome": "Gasolina"})
    await db.commit()
    items, total = await widget_crud.list(db, tenant_id=tid, limit=50, offset=0, search="diesel")
    assert total == 1
    assert items[0].nome == "Bomba Diesel"
    await widget_crud.soft_delete(db, tenant_id=tid, obj_id=a.id, user_id=uid)
    await db.commit()
    _, total_after = await widget_crud.list(db, tenant_id=tid, limit=50, offset=0, search="diesel")
    assert total_after == 0


async def test_update_bumps_version_and_requires_match(db, _widget_table):
    from app.crud.base import VersionConflictError

    tid = uuid.uuid4()
    uid = uuid.uuid4()
    obj = await widget_crud.create(db, tenant_id=tid, user_id=uid, data={"nome": "V1"})
    await db.commit()
    updated = await widget_crud.update(
        db, tenant_id=tid, obj_id=obj.id, user_id=uid, data={"nome": "V2"}, expected_version=1
    )
    await db.commit()
    assert updated.nome == "V2"
    assert updated.version == 2
    with pytest.raises(VersionConflictError):
        await widget_crud.update(
            db, tenant_id=tid, obj_id=obj.id, user_id=uid, data={"nome": "V3"}, expected_version=1
        )
    await db.rollback()

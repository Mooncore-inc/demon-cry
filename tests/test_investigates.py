from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from demon_cry.api import investigate as investigate_api
from demon_cry.api.dependencies.auth import get_current_user
from demon_cry.api.dependencies.config import get_registry
from demon_cry.api.dependencies.database import get_uow
from demon_cry.database.models.base import BaseModel
from demon_cry.database.uow import AppUnitOfWork


@pytest_asyncio.fixture
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
    yield async_sessionmaker(bind=engine, expire_on_commit=False)
    await engine.dispose()


def make_client(session_factory, user_id=1, registry=None):
    app = FastAPI()
    app.include_router(investigate_api.router)

    async def override_uow():
        async with session_factory() as session:
            uow = AppUnitOfWork(session)
            try:
                yield uow
            except BaseException:
                await uow.rollback()
                raise

    async def override_user():
        return SimpleNamespace(id=user_id)

    fake_registry = registry or AsyncMock()
    fake_registry.get_tools_schema = AsyncMock(return_value=[])
    if not isinstance(getattr(fake_registry, "execute", None), AsyncMock):
        fake_registry.execute = AsyncMock(
            return_value={"status": "success", "entities": {}, "errors": {}}
        )

    def override_registry():
        return fake_registry

    app.dependency_overrides[get_uow] = override_uow
    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_registry] = override_registry
    return TestClient(app), fake_registry


def test_repositories_share_one_session(session_factory):
    import asyncio

    async def _check():
        async with session_factory() as session:
            uow = AppUnitOfWork(session)
            assert uow.investigates.session is session
            assert uow.investigates_data.session is session

    asyncio.run(_check())


@pytest.mark.asyncio
async def test_create_and_get_persist(session_factory):
    async with session_factory() as session:
        uow = AppUnitOfWork(session)
        async with uow.transaction():
            inv = await uow.investigates.create(name="case-1", owner_id=1)
            await uow.investigates_data.create(
                investigate_id=inv.id,
                plugin_name="plug",
                status="success",
                entities={"a": 1},
                errors={},
            )

    async with session_factory() as session:
        uow = AppUnitOfWork(session)
        found = await uow.investigates.get(name="case-1", owner_id=1)
        assert found is not None
        rows = await uow.investigates_data.get_all(investigate_id=found.id)
        assert len(rows) == 1
        assert rows[0].plugin_name == "plug"


def test_crud_own_only():
    import asyncio

    engine_holder = {}

    async def _setup():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(BaseModel.metadata.create_all)
        engine_holder["engine"] = engine
        return async_sessionmaker(bind=engine, expire_on_commit=False)

    sf = asyncio.run(_setup())
    client_u1, _ = make_client(sf, user_id=1)
    client_u2, _ = make_client(sf, user_id=2)

    r1 = client_u1.post("/investigates/", json={"name": "u1-case-a"})
    assert r1.status_code == 201, r1.text
    id_a = r1.json()["id"]
    assert r1.json()["owner_id"] == 1

    r2 = client_u1.post("/investigates/", json={"name": "u1-case-b"})
    assert r2.status_code == 201

    r3 = client_u2.post("/investigates/", json={"name": "u2-case"})
    assert r3.status_code == 201

    lst = client_u1.get("/investigates/")
    assert lst.status_code == 200
    assert {i["name"] for i in lst.json()} == {"u1-case-a", "u1-case-b"}

    # чужое не видно
    assert client_u1.get(f"/investigates/{r3.json()['id']}").status_code == 404
    # своё видно
    assert client_u1.get(f"/investigates/{id_a}").status_code == 200

    # rename
    p = client_u1.patch(f"/investigates/{id_a}", json={"name": "renamed"})
    assert p.status_code == 200
    assert p.json()["name"] == "renamed"
    # чужой patch
    assert (
        client_u1.patch(
            f"/investigates/{r3.json()['id']}", json={"name": "x"}
        ).status_code
        == 404
    )


def test_execute_persists_run_and_list_data():
    import asyncio

    async def _setup():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(BaseModel.metadata.create_all)
        return async_sessionmaker(bind=engine, expire_on_commit=False)

    sf = asyncio.run(_setup())
    registry = AsyncMock()
    registry.get_tools_schema = AsyncMock(return_value=[])
    registry.execute = AsyncMock(
        return_value={"status": "success", "entities": {"ip": "1.1.1.1"}, "errors": {}}
    )
    client, _ = make_client(sf, user_id=7, registry=registry)

    inv = client.post("/investigates/", json={"name": "case"}).json()
    inv_id = inv["id"]

    ex = client.post(f"/investigates/{inv_id}/shodan/execute", json={"q": "x"})
    assert ex.status_code == 200, ex.text
    registry.execute.assert_called_once_with(tool_name="shodan", q="x")

    data = client.get(f"/investigates/{inv_id}/data")
    assert data.status_code == 200
    rows = data.json()
    assert len(rows) == 1
    assert rows[0]["plugin_name"] == "shodan"
    assert rows[0]["status"] == "success"
    assert rows[0]["entities"] == {"ip": "1.1.1.1"}

    # чужой execute — 404 и без записи
    other_registry = AsyncMock()
    other_registry.get_tools_schema = AsyncMock(return_value=[])
    other_registry.execute = AsyncMock(return_value={"status": "success"})
    client_other, _ = make_client(sf, user_id=999, registry=other_registry)
    assert (
        client_other.post(f"/investigates/{inv_id}/shodan/execute", json={}).status_code
        == 404
    )
    assert other_registry.execute.await_count == 0


def test_delete_removes_header_and_data():
    import asyncio

    async def _setup():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(BaseModel.metadata.create_all)
        return async_sessionmaker(bind=engine, expire_on_commit=False)

    sf = asyncio.run(_setup())
    client, _ = make_client(sf, user_id=3)

    inv_id = client.post("/investigates/", json={"name": "to-del"}).json()["id"]

    # подкинем run напрямую через UoW той же фабрики
    async def _seed():
        async with sf() as session:
            uow = AppUnitOfWork(session)
            async with uow.transaction():
                await uow.investigates_data.create(
                    investigate_id=inv_id,
                    plugin_name="p",
                    status="success",
                    entities={},
                    errors={},
                )

    asyncio.run(_seed())

    d = client.delete(f"/investigates/{inv_id}")
    assert d.status_code == 204
    assert client.get(f"/investigates/{inv_id}").status_code == 404
    assert client.get(f"/investigates/{inv_id}/data").status_code == 404


def test_llm_endpoint_gone():
    import asyncio

    async def _setup():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(BaseModel.metadata.create_all)
        return async_sessionmaker(bind=engine, expire_on_commit=False)

    sf = asyncio.run(_setup())
    client, _ = make_client(sf, user_id=1)
    r = client.post("/investigate", json={"target": "x"})
    assert r.status_code == 410

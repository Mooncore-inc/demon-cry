import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from demon_cry.api import investigate as investigate_api
from demon_cry.api.dependencies.auth import get_current_user
from demon_cry.api.dependencies.config import get_registry
from demon_cry.api.dependencies.database import get_uow
from demon_cry.database.models.base import BaseModel
from demon_cry.database.models.entities import (
    InvestigateEntityLinkModel,
    InvestigateEntityModel,
)
from demon_cry.database.uow import AppUnitOfWork


@pytest_asyncio.fixture
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
    yield async_sessionmaker(bind=engine, expire_on_commit=False)
    await engine.dispose()


def make_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    asyncio.run(_create_all(engine))
    return async_sessionmaker(bind=engine, expire_on_commit=False)


async def _create_all(engine):
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)


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


def registry_with(entities):
    registry = AsyncMock()
    registry.get_tools_schema = AsyncMock(return_value=[])
    registry.execute = AsyncMock(
        return_value={"status": "success", "entities": entities, "errors": {}}
    )
    return registry


def test_execute_creates_entities_with_run_id():
    sf = make_db()
    registry = registry_with([{"type": "IP", "value": " 1.1.1.1 ", "asn": 13335}])
    client, _ = make_client(sf, user_id=7, registry=registry)

    inv_id = client.post("/investigates/", json={"name": "case"}).json()["id"]
    assert (
        client.post(
            f"/investigates/{inv_id}/shodan/execute", json={"q": "x"}
        ).status_code
        == 200
    )

    entities = client.get(f"/investigates/{inv_id}/entities").json()
    assert len(entities) == 1
    entity = entities[0]
    assert entity["type"] == "ip"
    assert entity["value"] == "1.1.1.1"
    assert entity["data"] == {"asn": 13335}
    assert entity["source"] == "plugin"

    run_id = client.get(f"/investigates/{inv_id}/data").json()[0]["id"]
    assert entity["source_run_id"] == run_id
    # raw-лог остался без изменений (легаси-обёртка списка)
    assert client.get(f"/investigates/{inv_id}/data").json()[0]["entities"] == {
        "data": [{"type": "IP", "value": " 1.1.1.1 ", "asn": 13335}]
    }


def test_execute_legacy_shapes_extracted():
    sf = make_db()
    # dict-словарь и обёртка {"data": [...]}
    registry = registry_with({"ip": "1.1.1.1", "domain": "example.com"})
    client, _ = make_client(sf, user_id=1, registry=registry)
    inv_id = client.post("/investigates/", json={"name": "case"}).json()["id"]
    client.post(f"/investigates/{inv_id}/plug/execute", json={})
    types = {e["type"] for e in client.get(f"/investigates/{inv_id}/entities").json()}
    assert types == {"ip", "domain"}

    sf2 = make_db()
    registry2 = registry_with({"data": [{"type": "md5", "value": "deadbeef"}]})
    client2, _ = make_client(sf2, user_id=1, registry=registry2)
    inv2 = client2.post("/investigates/", json={"name": "case"}).json()["id"]
    client2.post(f"/investigates/{inv2}/plug/execute", json={})
    assert client2.get(f"/investigates/{inv2}/entities").json()[0]["type"] == "md5"


def test_execute_repeated_creates_duplicates_no_dedup():
    sf = make_db()
    registry = registry_with([{"type": "ip", "value": "1.1.1.1"}])
    client, _ = make_client(sf, user_id=1, registry=registry)
    inv_id = client.post("/investigates/", json={"name": "case"}).json()["id"]

    client.post(f"/investigates/{inv_id}/plug/execute", json={})
    client.post(f"/investigates/{inv_id}/plug/execute", json={})
    entities = client.get(f"/investigates/{inv_id}/entities").json()
    assert len(entities) == 2
    assert len({e["id"] for e in entities}) == 2


def test_execute_nested_body_back_compat():
    sf = make_db()
    registry = registry_with({})
    client, _ = make_client(sf, user_id=1, registry=registry)
    inv_id = client.post("/investigates/", json={"name": "case"}).json()["id"]

    body = {"params": {"q": "x", "tool_name": "ignore-me"}, "context_entity_ids": []}
    assert (
        client.post(f"/investigates/{inv_id}/plug/execute", json=body).status_code
        == 200
    )
    registry.execute.assert_called_once_with(tool_name="plug", q="x")


def test_execute_from_entity_creates_derived_links():
    sf = make_db()
    registry = registry_with([{"type": "ip", "value": "2.2.2.2", "ports": [80]}])
    client, _ = make_client(sf, user_id=1, registry=registry)
    inv_id = client.post("/investigates/", json={"name": "case"}).json()["id"]

    parent_id = client.post(
        f"/investigates/{inv_id}/entities",
        json={"type": "domain", "value": "example.com"},
    ).json()["id"]

    ex = client.post(
        f"/investigates/{inv_id}/plug/execute",
        json={"params": {"q": "example.com"}, "context_entity_ids": [parent_id]},
    )
    assert ex.status_code == 200, ex.text
    # в плагин контекст не пробрасывается
    registry.execute.assert_called_once_with(tool_name="plug", q="example.com")

    links = client.get(f"/investigates/{inv_id}/links").json()
    assert len(links) == 1
    link = links[0]
    assert link["source_id"] == parent_id
    assert link["relation"] == "derived_from"
    assert link["origin"] == "auto"
    assert link["source_run_id"] is not None

    child = [
        e
        for e in client.get(f"/investigates/{inv_id}/entities").json()
        if e["id"] != parent_id
    ][0]
    assert link["target_id"] == child["id"]
    assert child["data"] == {"ports": [80]}


def test_execute_echo_no_duplicate_node_or_link():
    sf = make_db()
    registry = registry_with([{"type": "IP", "value": "1.1.1.1", "x": 1}])
    client, _ = make_client(sf, user_id=1, registry=registry)
    inv_id = client.post("/investigates/", json={"name": "case"}).json()["id"]
    parent_id = client.post(
        f"/investigates/{inv_id}/entities",
        json={"type": "ip", "value": "1.1.1.1"},
    ).json()["id"]

    ex = client.post(
        f"/investigates/{inv_id}/plug/execute",
        json={"params": {}, "context_entity_ids": [parent_id]},
    )
    assert ex.status_code == 200
    assert len(client.get(f"/investigates/{inv_id}/entities").json()) == 1
    assert client.get(f"/investigates/{inv_id}/links").json() == []


def test_execute_without_context_creates_entities_without_links():
    sf = make_db()
    registry = registry_with([{"type": "ip", "value": "3.3.3.3"}])
    client, _ = make_client(sf, user_id=1, registry=registry)
    inv_id = client.post("/investigates/", json={"name": "case"}).json()["id"]

    assert (
        client.post(f"/investigates/{inv_id}/plug/execute", json={}).status_code == 200
    )
    assert len(client.get(f"/investigates/{inv_id}/entities").json()) == 1
    assert client.get(f"/investigates/{inv_id}/links").json() == []


def test_execute_foreign_context_entity_rejected():
    sf = make_db()
    registry = registry_with({})
    client, _ = make_client(sf, user_id=1, registry=registry)
    inv_id = client.post("/investigates/", json={"name": "case"}).json()["id"]
    other_inv = client.post("/investigates/", json={"name": "other"}).json()["id"]
    foreign_id = client.post(
        f"/investigates/{other_inv}/entities", json={"value": "x"}
    ).json()["id"]

    ex = client.post(
        f"/investigates/{inv_id}/plug/execute",
        json={"params": {}, "context_entity_ids": [foreign_id]},
    )
    assert ex.status_code == 400
    assert registry.execute.await_count == 0

    missing = client.post(
        f"/investigates/{inv_id}/plug/execute",
        json={"params": {}, "context_entity_ids": [99999]},
    )
    assert missing.status_code == 400


def test_execute_too_many_context_ids():
    sf = make_db()
    registry = registry_with({})
    client, _ = make_client(sf, user_id=1, registry=registry)
    inv_id = client.post("/investigates/", json={"name": "case"}).json()["id"]
    ids = [
        client.post(f"/investigates/{inv_id}/entities", json={"value": f"n{i}"}).json()[
            "id"
        ]
        for i in range(101)
    ]
    ex = client.post(
        f"/investigates/{inv_id}/plug/execute",
        json={"params": {}, "context_entity_ids": ids},
    )
    assert ex.status_code == 400


def test_run_error_still_extracts_entities():
    sf = make_db()
    registry = AsyncMock()
    registry.get_tools_schema = AsyncMock(return_value=[])
    registry.execute = AsyncMock(
        return_value={
            "status": "error",
            "entities": [{"type": "ip", "value": "4.4.4.4"}],
            "errors": {"msg": "partial"},
        }
    )
    client, _ = make_client(sf, user_id=1, registry=registry)
    inv_id = client.post("/investigates/", json={"name": "case"}).json()["id"]
    client.post(f"/investigates/{inv_id}/plug/execute", json={})
    entities = client.get(f"/investigates/{inv_id}/entities").json()
    assert [e["value"] for e in entities] == ["4.4.4.4"]


def test_manual_entities_dup_allowed_and_patch():
    sf = make_db()
    client, _ = make_client(sf, user_id=2)
    inv_id = client.post("/investigates/", json={"name": "case"}).json()["id"]

    a = client.post(
        f"/investigates/{inv_id}/entities",
        json={"type": "Person", "value": "John Doe", "data": {"age": 30}},
    )
    assert a.status_code == 201, a.text
    b = client.post(
        f"/investigates/{inv_id}/entities",
        json={"type": "Person", "value": "John Doe"},
    )
    assert b.status_code == 201
    assert a.json()["id"] != b.json()["id"]
    assert (a.json()["type"], b.json()["type"]) == ("person", "person")
    assert a.json()["source"] == "manual"
    assert a.json()["source_run_id"] is None

    patched = client.patch(
        f"/investigates/{inv_id}/entities/{a.json()['id']}",
        json={"label": "Suspect", "data": {"age": 31}},
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["label"] == "Suspect"
    assert patched.json()["data"] == {"age": 31}
    assert patched.json()["value"] == "John Doe"

    empty_patch = client.patch(
        f"/investigates/{inv_id}/entities/{a.json()['id']}", json={}
    )
    assert empty_patch.status_code == 422
    empty_value = client.post(f"/investigates/{inv_id}/entities", json={"value": "   "})
    assert empty_value.status_code == 422

    # фильтры списка
    lst = client.get(f"/investigates/{inv_id}/entities", params={"search": "John"})
    assert lst.status_code == 200
    assert len(lst.json()) == 2
    lst_type = client.get(f"/investigates/{inv_id}/entities", params={"type": "person"})
    assert len(lst_type.json()) == 2


def test_manual_links_crud_and_conflicts():
    sf = make_db()
    client, _ = make_client(sf, user_id=3)
    inv_id = client.post("/investigates/", json={"name": "case"}).json()["id"]
    ids = []
    for i in range(2):
        ids.append(
            client.post(
                f"/investigates/{inv_id}/entities", json={"value": f"n{i}"}
            ).json()["id"]
        )
    a, b = ids

    created = client.post(
        f"/investigates/{inv_id}/entities/{a}/links",
        json={"target_id": b, "relation": "related_to", "data": {"note": "dup?"}},
    )
    assert created.status_code == 201, created.text
    assert created.json()["origin"] == "manual"

    dup = client.post(
        f"/investigates/{inv_id}/entities/{a}/links", json={"target_id": b}
    )
    assert dup.status_code == 409

    # другая relation/origin — разрешены
    other_relation = client.post(
        f"/investigates/{inv_id}/entities/{a}/links",
        json={"target_id": b, "relation": "same_person"},
    )
    assert other_relation.status_code == 201

    self_link = client.post(
        f"/investigates/{inv_id}/entities/{a}/links", json={"target_id": a}
    )
    assert self_link.status_code == 400

    bad_relation = client.post(
        f"/investigates/{inv_id}/entities/{a}/links",
        json={"target_id": b, "relation": "WRONG!"},
    )
    assert bad_relation.status_code == 422

    # список с фильтрами
    filtered = client.get(
        f"/investigates/{inv_id}/links",
        params={"origin": "manual", "relation": "related_to"},
    )
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1

    link_id = filtered.json()[0]["id"]
    patched = client.patch(
        f"/investigates/{inv_id}/links/{link_id}", json={"data": {"note": "ok"}}
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["data"] == {"note": "ok"}
    assert patched.json()["relation"] == "related_to"

    deleted = client.delete(f"/investigates/{inv_id}/links/{link_id}")
    assert deleted.status_code == 204
    remaining = client.get(
        f"/investigates/{inv_id}/links", params={"relation": "related_to"}
    )
    assert remaining.json() == []


def test_entity_detail_with_links():
    sf = make_db()
    client, _ = make_client(sf, user_id=1)
    inv_id = client.post("/investigates/", json={"name": "case"}).json()["id"]
    a = client.post(f"/investigates/{inv_id}/entities", json={"value": "a"}).json()[
        "id"
    ]
    b = client.post(f"/investigates/{inv_id}/entities", json={"value": "b"}).json()[
        "id"
    ]
    client.post(f"/investigates/{inv_id}/entities/{a}/links", json={"target_id": b})
    detail = client.get(f"/investigates/{inv_id}/entities/{a}")
    assert detail.status_code == 200
    body = detail.json()
    assert len(body["outgoing"]) == 1
    assert body["outgoing"][0]["target_id"] == b
    assert body["incoming"] == []
    detail_b = client.get(f"/investigates/{inv_id}/entities/{b}").json()
    assert len(detail_b["incoming"]) == 1


def test_delete_entity_removes_links_but_keeps_targets():
    sf = make_db()
    client, _ = make_client(sf, user_id=5)
    inv_id = client.post("/investigates/", json={"name": "case"}).json()["id"]
    a = client.post(f"/investigates/{inv_id}/entities", json={"value": "child"}).json()[
        "id"
    ]
    parent = client.post(
        f"/investigates/{inv_id}/entities", json={"value": "parent"}
    ).json()["id"]
    client.post(
        f"/investigates/{inv_id}/entities/{parent}/links", json={"target_id": a}
    )
    link_id = client.get(f"/investigates/{inv_id}/links").json()[0]["id"]
    assert client.delete(f"/investigates/{inv_id}/links/{link_id}").status_code == 204

    # разорвали derived_from — нода осталась самостоятельной
    assert (
        client.get(f"/investigates/{inv_id}/entities/{a}").json()["source"] == "manual"
    )
    # перелинковка вручную
    assert (
        client.post(
            f"/investigates/{inv_id}/entities/{parent}/links", json={"target_id": a}
        ).status_code
        == 201
    )

    # удаление энтити чистит её связи, вторая нода жива
    assert client.delete(f"/investigates/{inv_id}/entities/{a}").status_code == 204
    assert client.get(f"/investigates/{inv_id}/entities/{a}").status_code == 404
    assert (
        client.get(f"/investigates/{inv_id}/links", params={"limit": 100}).json() == []
    )
    assert (
        client.get(f"/investigates/{inv_id}/entities/{parent}").json()["value"]
        == "parent"
    )


def test_delete_investigate_cascades_entities_and_links():
    sf = make_db()
    client, _ = make_client(sf, user_id=6)
    inv_id = client.post("/investigates/", json={"name": "case"}).json()["id"]
    a = client.post(f"/investigates/{inv_id}/entities", json={"value": "a"}).json()[
        "id"
    ]
    b = client.post(f"/investigates/{inv_id}/entities", json={"value": "b"}).json()[
        "id"
    ]
    client.post(f"/investigates/{inv_id}/entities/{a}/links", json={"target_id": b})

    assert client.delete(f"/investigates/{inv_id}").status_code == 204

    async def _check():
        async with sf() as session:
            entities = (
                (await session.execute(select(InvestigateEntityModel))).scalars().all()
            )
            links = (
                (await session.execute(select(InvestigateEntityLinkModel)))
                .scalars()
                .all()
            )
            assert entities == []
            assert links == []

    asyncio.run(_check())
    assert client.get(f"/investigates/{inv_id}/entities").status_code == 404


def test_graph_shape_limits_and_types_filter():
    sf = make_db()
    registry = registry_with([{"type": "ip", "value": "9.9.9.9"}])
    client, _ = make_client(sf, user_id=1, registry=registry)
    inv_id = client.post("/investigates/", json={"name": "case"}).json()["id"]

    ip1 = client.post(
        f"/investigates/{inv_id}/entities", json={"type": "ip", "value": "1.1.1.1"}
    ).json()["id"]
    ip2 = client.post(
        f"/investigates/{inv_id}/entities", json={"type": "ip", "value": "2.2.2.2"}
    ).json()["id"]
    domain = client.post(
        f"/investigates/{inv_id}/entities", json={"type": "domain", "value": "x.io"}
    ).json()["id"]
    client.post(f"/investigates/{inv_id}/entities/{ip1}/links", json={"target_id": ip2})
    client.post(
        f"/investigates/{inv_id}/entities/{ip1}/links",
        json={"target_id": domain, "relation": "resolves"},
    )
    client.post(
        f"/investigates/{inv_id}/plug/execute",
        json={"params": {}, "context_entity_ids": [ip1]},
    )

    graph = client.get(f"/investigates/{inv_id}/graph")
    assert graph.status_code == 200
    body = graph.json()
    assert len(body["nodes"]) == 4  # ip1, ip2, domain, 9.9.9.9
    assert len(body["edges"]) == 3  # ip1->ip2, ip1->domain, ip1->9.9.9.9

    limited = client.get(f"/investigates/{inv_id}/graph", params={"limit": 1}).json()
    assert len(limited["nodes"]) == 1
    # edges только между вошедшими узлами
    node_ids = {n["id"] for n in limited["nodes"]}
    assert all(
        e["source_id"] in node_ids and e["target_id"] in node_ids
        for e in limited["edges"]
    )

    typed = client.get(f"/investigates/{inv_id}/graph", params={"types": "ip"}).json()
    assert {n["type"] for n in typed["nodes"]} == {"ip"}
    assert len(typed["nodes"]) == 3
    assert all(
        e["source_id"] in {n["id"] for n in typed["nodes"]}
        and e["target_id"] in {n["id"] for n in typed["nodes"]}
        for e in typed["edges"]
    )


def test_entities_endpoints_respect_ownership():
    sf = make_db()
    client_owner, _ = make_client(sf, user_id=1)
    inv_id = client_owner.post("/investigates/", json={"name": "case"}).json()["id"]
    ent_id = client_owner.post(
        f"/investigates/{inv_id}/entities", json={"value": "secret"}
    ).json()["id"]

    client_stranger, _ = make_client(sf, user_id=999)
    assert (
        client_stranger.post(
            f"/investigates/{inv_id}/entities", json={"value": "x"}
        ).status_code
        == 404
    )
    assert (
        client_stranger.get(f"/investigates/{inv_id}/entities/{ent_id}").status_code
        == 404
    )
    assert client_stranger.get(f"/investigates/{inv_id}/graph").status_code == 404


def test_session_sharing_after_repo_addition(session_factory):
    async def _check():
        async with session_factory() as session:
            uow = AppUnitOfWork(session)
            assert uow.entities.session is session
            assert uow.entity_links.session is session

    asyncio.run(_check())

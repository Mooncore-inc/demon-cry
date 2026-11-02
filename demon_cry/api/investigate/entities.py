from fastapi import APIRouter, HTTPException, Query

from demon_cry.api.dependencies import CurrentUser, UoWDep
from demon_cry.api.investigate.common import LINKS_LIST_LIMIT, get_entity, get_owned
from demon_cry.api.schemas.entities import (
    EntityCreate,
    EntityDetailResponse,
    EntityResponse,
    EntityUpdate,
)
from demon_cry.services.entities import normalize_type

entities_router = APIRouter()


@entities_router.post(
    path="/investigates/{investigate_id}/entities",
    status_code=201,
    response_model=EntityResponse,
)
async def create_entity(
    investigate_id: int,
    body: EntityCreate,
    uow: UoWDep,
    user: CurrentUser,
):
    inv = await get_owned(uow, investigate_id, user)
    value = body.value.strip()
    if not value:
        raise HTTPException(status_code=422, detail="value must not be empty")
    async with uow.transaction():
        return await uow.entities.create(
            investigate_id=inv.id,
            type=normalize_type(body.type) if body.type else None,
            value=value[:1024],
            label=body.label,
            data=body.data,
            source="manual",
            source_run_id=None,
        )


@entities_router.get(
    path="/investigates/{investigate_id}/entities",
    response_model=list[EntityResponse],
)
async def list_entities(
    investigate_id: int,
    uow: UoWDep,
    user: CurrentUser,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    type: str | None = Query(default=None, max_length=64),
    search: str | None = Query(default=None, max_length=256),
):
    inv = await get_owned(uow, investigate_id, user)
    return await uow.entities.search(
        inv.id,
        limit=limit,
        offset=offset,
        type=type,
        search=search,
    )


@entities_router.get(
    path="/investigates/{investigate_id}/entities/{entity_id}",
    response_model=EntityDetailResponse,
)
async def get_entity_detail(
    investigate_id: int,
    entity_id: int,
    uow: UoWDep,
    user: CurrentUser,
):
    inv = await get_owned(uow, investigate_id, user)
    entity = await get_entity(uow, inv.id, entity_id)
    incoming = await uow.entity_links.get_all(
        investigate_id=inv.id, target_id=entity.id, limit=LINKS_LIST_LIMIT
    )
    outgoing = await uow.entity_links.get_all(
        investigate_id=inv.id, source_id=entity.id, limit=LINKS_LIST_LIMIT
    )
    payload = EntityResponse.model_validate(entity).model_dump()
    payload["incoming"] = incoming
    payload["outgoing"] = outgoing
    return EntityDetailResponse.model_validate(payload)


@entities_router.patch(
    path="/investigates/{investigate_id}/entities/{entity_id}",
    response_model=EntityResponse,
)
async def update_entity(
    investigate_id: int,
    entity_id: int,
    body: EntityUpdate,
    uow: UoWDep,
    user: CurrentUser,
):
    inv = await get_owned(uow, investigate_id, user)
    entity = await get_entity(uow, inv.id, entity_id)
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=422, detail="Nothing to update")
    async with uow.transaction():
        return await uow.entities.update(entity, **updates)


@entities_router.delete(
    path="/investigates/{investigate_id}/entities/{entity_id}", status_code=204
)
async def delete_entity(
    investigate_id: int,
    entity_id: int,
    uow: UoWDep,
    user: CurrentUser,
):
    inv = await get_owned(uow, investigate_id, user)
    entity = await get_entity(uow, inv.id, entity_id)
    async with uow.transaction():
        await uow.entity_links.delete_for_entity(entity.id)
        await uow.entities.delete(entity)

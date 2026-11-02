from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from demon_cry.api.dependencies import CurrentUser, UoWDep
from demon_cry.api.investigate.common import get_entity, get_link, get_owned
from demon_cry.api.schemas.entities import (
    EntityLinkCreate,
    EntityLinkResponse,
    EntityLinkUpdate,
)

links_router = APIRouter()


@links_router.post(
    path="/investigates/{investigate_id}/entities/{source_id}/links",
    status_code=201,
    response_model=EntityLinkResponse,
)
async def create_entity_link(
    investigate_id: int,
    source_id: int,
    body: EntityLinkCreate,
    uow: UoWDep,
    user: CurrentUser,
):
    inv = await get_owned(uow, investigate_id, user)
    source = await get_entity(uow, inv.id, source_id)
    if body.target_id == source.id:
        raise HTTPException(
            status_code=400, detail="source_id must differ from target_id"
        )
    target = await uow.entities.get_by_id(body.target_id)
    if target is None or target.investigate_id != inv.id:
        raise HTTPException(
            status_code=400, detail="target_id not found in investigation"
        )
    duplicate = await uow.entity_links.get_duplicate(
        investigate_id=inv.id,
        source_id=source.id,
        target_id=body.target_id,
        relation=body.relation,
        origin="manual",
    )
    if duplicate is not None:
        raise HTTPException(status_code=409, detail="Link already exists")
    async with uow.transaction():
        return await uow.entity_links.create(
            investigate_id=inv.id,
            source_id=source.id,
            target_id=body.target_id,
            relation=body.relation,
            origin="manual",
            source_run_id=None,
            data=body.data,
        )


@links_router.get(
    path="/investigates/{investigate_id}/links",
    response_model=list[EntityLinkResponse],
)
async def list_entity_links(
    investigate_id: int,
    uow: UoWDep,
    user: CurrentUser,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    origin: Literal["auto", "manual"] | None = Query(default=None),
    relation: str | None = Query(default=None, max_length=64),
    source_id: int | None = Query(default=None),
    target_id: int | None = Query(default=None),
):
    inv = await get_owned(uow, investigate_id, user)
    filters: dict = {"investigate_id": inv.id}
    if origin is not None:
        filters["origin"] = origin
    if relation is not None:
        filters["relation"] = relation
    if source_id is not None:
        filters["source_id"] = source_id
    if target_id is not None:
        filters["target_id"] = target_id
    return await uow.entity_links.get_all(limit=limit, offset=offset, **filters)


@links_router.patch(
    path="/investigates/{investigate_id}/links/{link_id}",
    response_model=EntityLinkResponse,
)
async def update_entity_link(
    investigate_id: int,
    link_id: int,
    body: EntityLinkUpdate,
    uow: UoWDep,
    user: CurrentUser,
):
    inv = await get_owned(uow, investigate_id, user)
    link = await get_link(uow, inv.id, link_id)
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=422, detail="Nothing to update")
    if "relation" in updates:
        duplicate = await uow.entity_links.get_duplicate(
            investigate_id=inv.id,
            source_id=link.source_id,
            target_id=link.target_id,
            relation=updates["relation"],
            origin=link.origin,
        )
        if duplicate is not None and duplicate.id != link.id:
            raise HTTPException(status_code=409, detail="Link already exists")
    async with uow.transaction():
        return await uow.entity_links.update(link, **updates)


@links_router.delete(
    path="/investigates/{investigate_id}/links/{link_id}", status_code=204
)
async def delete_entity_link(
    investigate_id: int,
    link_id: int,
    uow: UoWDep,
    user: CurrentUser,
):
    inv = await get_owned(uow, investigate_id, user)
    link = await get_link(uow, inv.id, link_id)
    async with uow.transaction():
        await uow.entity_links.delete(link)

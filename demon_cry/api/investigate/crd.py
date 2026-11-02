from fastapi import APIRouter, HTTPException, Query

from demon_cry.api.dependencies import CurrentUser, UoWDep
from demon_cry.api.investigate.common import get_owned
from demon_cry.api.schemas.investigates import (
    InvestigateCreate,
    InvestigateResponse,
    InvestigateUpdate,
)

crd_router = APIRouter()


@crd_router.post(
    path="/investigates/", status_code=201, response_model=InvestigateResponse
)
async def create_investigate(
    body: InvestigateCreate,
    uow: UoWDep,
    user: CurrentUser,
):
    async with uow.transaction():
        return await uow.investigates.create(name=body.name, owner_id=user.id)


@crd_router.get(path="/investigates/", response_model=list[InvestigateResponse])
async def list_investigates(
    uow: UoWDep,
    user: CurrentUser,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    return await uow.investigates.get_all(limit=limit, offset=offset, owner_id=user.id)


@crd_router.get(
    path="/investigates/{investigate_id}", response_model=InvestigateResponse
)
async def get_investigate(
    investigate_id: int,
    uow: UoWDep,
    user: CurrentUser,
):
    return await get_owned(uow, investigate_id, user)


@crd_router.patch(
    path="/investigates/{investigate_id}", response_model=InvestigateResponse
)
async def update_investigate(
    investigate_id: int,
    body: InvestigateUpdate,
    uow: UoWDep,
    user: CurrentUser,
):
    inv = await get_owned(uow, investigate_id, user)
    async with uow.transaction():
        return await uow.investigates.update(inv, name=body.name)


@crd_router.delete(path="/investigates/{investigate_id}", status_code=204)
async def delete_investigate(
    investigate_id: int,
    uow: UoWDep,
    user: CurrentUser,
):
    inv = await get_owned(uow, investigate_id, user)
    async with uow.transaction():
        await uow.entity_links.delete_by_investigation(inv.id)
        await uow.entities.delete_by_investigation(inv.id)
        await uow.investigates_data.delete_by_investigation(inv.id)
        await uow.investigates.delete(inv)


@crd_router.post(path="/investigate", status_code=410)
async def investigate_gone():
    raise HTTPException(
        status_code=410,
        detail="LLM investigation is disabled, use /investigates CRUD + execute",
    )

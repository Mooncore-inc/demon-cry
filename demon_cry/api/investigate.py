import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import delete

from demon_cry.api.dependencies import AppRegistry, CurrentUser, UoWDep
from demon_cry.api.schemas.investigates import (
    InvestigateCreate,
    InvestigateDataResponse,
    InvestigateResponse,
    InvestigateUpdate,
)
from demon_cry.core.plugin_registry import ToolDefinition
from demon_cry.database.models.investigate import (
    InvestigatesDataModel,
    InvestigatesModel,
)
from demon_cry.database.models.users import UserModel
from demon_cry.database.uow import AppUnitOfWork

router = APIRouter()

logger = logging.getLogger(__name__)


async def _get_owned(
    uow: AppUnitOfWork, investigate_id: int, user: UserModel
) -> InvestigatesModel:
    inv = await uow.investigates.get_by_id(investigate_id)
    if inv is None or inv.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return inv


def _as_dict(value: object) -> dict:
    if isinstance(value, dict):
        return value
    return {"data": value}


@router.post(path="/investigates/", status_code=201, response_model=InvestigateResponse)
async def create_investigate(
    body: InvestigateCreate,
    uow: UoWDep,
    user: CurrentUser,
):
    async with uow.transaction():
        return await uow.investigates.create(name=body.name, owner_id=user.id)


@router.get(path="/investigates/", response_model=list[InvestigateResponse])
async def list_investigates(
    uow: UoWDep,
    user: CurrentUser,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    return await uow.investigates.get_all(limit=limit, offset=offset, owner_id=user.id)


@router.get(path="/investigates/{investigate_id}", response_model=InvestigateResponse)
async def get_investigate(
    investigate_id: int,
    uow: UoWDep,
    user: CurrentUser,
):
    return await _get_owned(uow, investigate_id, user)


@router.patch(path="/investigates/{investigate_id}", response_model=InvestigateResponse)
async def update_investigate(
    investigate_id: int,
    body: InvestigateUpdate,
    uow: UoWDep,
    user: CurrentUser,
):
    inv = await _get_owned(uow, investigate_id, user)
    async with uow.transaction():
        return await uow.investigates.update(inv, name=body.name)


@router.delete(path="/investigates/{investigate_id}", status_code=204)
async def delete_investigate(
    investigate_id: int,
    uow: UoWDep,
    user: CurrentUser,
):
    inv = await _get_owned(uow, investigate_id, user)
    async with uow.transaction():
        await uow.session.execute(
            delete(InvestigatesDataModel).where(
                InvestigatesDataModel.investigate_id == inv.id
            )
        )
        await uow.investigates.delete(inv)


@router.post(path="/investigates/{investigate_id}/{tool_name}/execute")
async def investigate_tool_execute(
    investigate_id: int,
    tool_name: str,
    req: dict,
    registry: AppRegistry,
    uow: UoWDep,
    user: CurrentUser,
):
    inv = await _get_owned(uow, investigate_id, user)
    result = await registry.execute(tool_name=tool_name, **req)
    if not isinstance(result, dict):
        result = {"data": result}
    status = str(result.get("status", "error" if "error" in result else "success"))
    async with uow.transaction():
        await uow.investigates_data.create(
            investigate_id=inv.id,
            plugin_name=tool_name,
            status=status,
            entities=_as_dict(result.get("entities", {})),
            errors=_as_dict(result.get("errors", {})),
        )
    return result


@router.get(
    path="/investigates/{investigate_id}/data",
    response_model=list[InvestigateDataResponse],
)
async def list_investigate_data(
    investigate_id: int,
    uow: UoWDep,
    user: CurrentUser,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    inv = await _get_owned(uow, investigate_id, user)
    return await uow.investigates_data.get_all(
        limit=limit, offset=offset, investigate_id=inv.id
    )


@router.post(path="/investigate", status_code=410)
async def investigate_gone():
    raise HTTPException(
        status_code=410,
        detail="LLM investigation is disabled, use /investigates CRUD + execute",
    )


class ToolsResponse(BaseModel):
    tools: list[ToolDefinition]


@router.get(path="/investigate/tools")
async def tools(
    registry: AppRegistry,
    user: CurrentUser,
):
    tools = await registry.get_tools_schema()
    return ToolsResponse(tools=tools)

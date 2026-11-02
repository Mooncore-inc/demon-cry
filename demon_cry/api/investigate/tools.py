from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel

from demon_cry.api.dependencies import AppRegistry, CurrentUser, UoWDep
from demon_cry.api.investigate.common import CONTEXT_IDS_LIMIT, as_dict, get_owned
from demon_cry.api.schemas.investigates import (
    InvestigateDataResponse,
    InvestigateExecuteRequest,
)
from demon_cry.core.plugin_registry import ToolDefinition
from demon_cry.database.models.entities import InvestigateEntityModel
from demon_cry.services.entities import create_entities_from_run

tools_router = APIRouter()


class ToolsResponse(BaseModel):
    tools: list[ToolDefinition]


@tools_router.get(path="/investigate/tools")
async def tools(
    registry: AppRegistry,
    user: CurrentUser,
):
    tools = await registry.get_tools_schema()
    return ToolsResponse(tools=tools)


@tools_router.post(path="/investigates/{investigate_id}/{tool_name}/execute")
async def investigate_tool_execute(
    investigate_id: int,
    tool_name: Annotated[str, Path(max_length=128)],
    req: InvestigateExecuteRequest,
    registry: AppRegistry,
    uow: UoWDep,
    user: CurrentUser,
):
    inv = await get_owned(uow, investigate_id, user)
    params = dict(req.params)
    params.pop("tool_name", None)

    parents: list[InvestigateEntityModel] = []
    if req.context_entity_ids:
        unique_ids = list(dict.fromkeys(req.context_entity_ids))
        if len(unique_ids) > CONTEXT_IDS_LIMIT:
            raise HTTPException(
                status_code=400,
                detail=f"Too many context_entity_ids (max {CONTEXT_IDS_LIMIT})",
            )
        for entity_id in unique_ids:
            parent = await uow.entities.get_by_id(entity_id)
            if parent is None or parent.investigate_id != inv.id:
                raise HTTPException(
                    status_code=400,
                    detail=f"Entity {entity_id} not found in investigation {inv.id}",
                )
            parents.append(parent)

    result = await registry.execute(tool_name=tool_name, **params)
    if not isinstance(result, dict):
        result = {"data": result}
    status = str(result.get("status", "error" if "error" in result else "success"))
    status = status[:32]
    async with uow.transaction():
        row = await uow.investigates_data.create(
            investigate_id=inv.id,
            plugin_name=tool_name,
            status=status,
            entities=as_dict(result.get("entities", {})),
            errors=as_dict(result.get("errors", {})),
        )
        await create_entities_from_run(
            uow=uow,
            investigate_id=inv.id,
            run_id=row.id,
            entities_raw=result.get("entities"),
            parents=parents,
        )
    return result


@tools_router.get(
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
    inv = await get_owned(uow, investigate_id, user)
    return await uow.investigates_data.get_all(
        limit=limit, offset=offset, investigate_id=inv.id
    )

from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel

from demon_cry.api.dependencies import AppRegistry, CurrentUser, UoWDep
from demon_cry.api.schemas.entities import (
    EntityCreate,
    EntityDetailResponse,
    EntityGraphResponse,
    EntityLinkCreate,
    EntityLinkResponse,
    EntityLinkUpdate,
    EntityResponse,
    EntityUpdate,
)
from demon_cry.api.schemas.investigates import (
    InvestigateCreate,
    InvestigateDataResponse,
    InvestigateExecuteRequest,
    InvestigateResponse,
    InvestigateUpdate,
)
from demon_cry.core.plugin_registry import ToolDefinition
from demon_cry.database.models.entities import (
    InvestigateEntityLinkModel,
    InvestigateEntityModel,
)
from demon_cry.database.models.investigate import InvestigatesModel
from demon_cry.database.models.users import UserModel
from demon_cry.database.uow import AppUnitOfWork
from demon_cry.services.entities import create_entities_from_run, normalize_type

router = APIRouter()

CONTEXT_IDS_LIMIT = 100
GRAPH_NODE_LIMIT_DEFAULT = 500
GRAPH_EDGE_LIMIT = 5000
LINKS_LIST_LIMIT = 1000


async def _get_owned(
    uow: AppUnitOfWork, investigate_id: int, user: UserModel
) -> InvestigatesModel:
    inv = await uow.investigates.get_by_id(investigate_id)
    if inv is None or inv.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return inv


async def _get_entity(
    uow: AppUnitOfWork, investigate_id: int, entity_id: int
) -> InvestigateEntityModel:
    entity = await uow.entities.get_by_id(entity_id)
    if entity is None or entity.investigate_id != investigate_id:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


async def _get_link(
    uow: AppUnitOfWork, investigate_id: int, link_id: int
) -> InvestigateEntityLinkModel:
    link = await uow.entity_links.get_by_id(link_id)
    if link is None or link.investigate_id != investigate_id:
        raise HTTPException(status_code=404, detail="Link not found")
    return link


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
        await uow.entity_links.delete_by_investigation(inv.id)
        await uow.entities.delete_by_investigation(inv.id)
        await uow.investigates_data.delete_by_investigation(inv.id)
        await uow.investigates.delete(inv)


@router.post(path="/investigates/{investigate_id}/{tool_name}/execute")
async def investigate_tool_execute(
    investigate_id: int,
    tool_name: Annotated[str, Path(max_length=128)],
    req: InvestigateExecuteRequest,
    registry: AppRegistry,
    uow: UoWDep,
    user: CurrentUser,
):
    inv = await _get_owned(uow, investigate_id, user)
    params = dict(req.params)
    params.pop("tool_name", None)

    parents: list[InvestigateEntityModel] = []
    if req.context_entity_ids:
        # дубли id игнорируем, сохраняем порядок
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
            entities=_as_dict(result.get("entities", {})),
            errors=_as_dict(result.get("errors", {})),
        )
        await create_entities_from_run(
            uow=uow,
            investigate_id=inv.id,
            run_id=row.id,
            entities_raw=result.get("entities"),
            parents=parents,
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


# --- Энтити ---------------------------------------------------------------


@router.post(
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
    inv = await _get_owned(uow, investigate_id, user)
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


@router.get(
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
    inv = await _get_owned(uow, investigate_id, user)
    return await uow.entities.search(
        inv.id,
        limit=limit,
        offset=offset,
        type=type,
        search=search,
    )


@router.get(
    path="/investigates/{investigate_id}/entities/{entity_id}",
    response_model=EntityDetailResponse,
)
async def get_entity(
    investigate_id: int,
    entity_id: int,
    uow: UoWDep,
    user: CurrentUser,
):
    inv = await _get_owned(uow, investigate_id, user)
    entity = await _get_entity(uow, inv.id, entity_id)
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


@router.patch(
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
    inv = await _get_owned(uow, investigate_id, user)
    entity = await _get_entity(uow, inv.id, entity_id)
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=422, detail="Nothing to update")
    # type/value иммутабельны по контракту; схема их просто не содержит
    async with uow.transaction():
        return await uow.entities.update(entity, **updates)


@router.delete(
    path="/investigates/{investigate_id}/entities/{entity_id}", status_code=204
)
async def delete_entity(
    investigate_id: int,
    entity_id: int,
    uow: UoWDep,
    user: CurrentUser,
):
    inv = await _get_owned(uow, investigate_id, user)
    entity = await _get_entity(uow, inv.id, entity_id)
    async with uow.transaction():
        await uow.entity_links.delete_for_entity(entity.id)
        await uow.entities.delete(entity)


# --- Связи ---------------------------------------------------------------


@router.post(
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
    inv = await _get_owned(uow, investigate_id, user)
    source = await _get_entity(uow, inv.id, source_id)
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


@router.get(
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
    inv = await _get_owned(uow, investigate_id, user)
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


@router.patch(
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
    inv = await _get_owned(uow, investigate_id, user)
    link = await _get_link(uow, inv.id, link_id)
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


@router.delete(path="/investigates/{investigate_id}/links/{link_id}", status_code=204)
async def delete_entity_link(
    investigate_id: int,
    link_id: int,
    uow: UoWDep,
    user: CurrentUser,
):
    inv = await _get_owned(uow, investigate_id, user)
    link = await _get_link(uow, inv.id, link_id)
    async with uow.transaction():
        await uow.entity_links.delete(link)


# --- Граф ---------------------------------------------------------------


@router.get(
    path="/investigates/{investigate_id}/graph",
    response_model=EntityGraphResponse,
)
async def get_entity_graph(
    investigate_id: int,
    uow: UoWDep,
    user: CurrentUser,
    limit: int = Query(
        default=GRAPH_NODE_LIMIT_DEFAULT, ge=1, le=GRAPH_NODE_LIMIT_DEFAULT * 2
    ),
    offset: int = Query(default=0, ge=0),
    types: str | None = Query(default=None, max_length=2048),
):
    inv = await _get_owned(uow, investigate_id, user)
    type_list = None
    if types is not None:
        type_list = [t.strip() for t in types.split(",") if t.strip()] or None
    nodes = await uow.entities.search(
        inv.id,
        limit=limit,
        offset=offset,
        types=type_list,
    )
    node_ids = {node.id for node in nodes}
    edges = []
    if node_ids:
        edges = await uow.entity_links.get_edges_between(
            inv.id, node_ids, limit=GRAPH_EDGE_LIMIT
        )
    return EntityGraphResponse(nodes=nodes, edges=edges)


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

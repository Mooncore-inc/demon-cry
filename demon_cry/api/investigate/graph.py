from fastapi import APIRouter, Query

from demon_cry.api.dependencies import CurrentUser, UoWDep
from demon_cry.api.investigate.common import (
    GRAPH_EDGE_LIMIT,
    GRAPH_NODE_LIMIT_DEFAULT,
    get_owned,
)
from demon_cry.api.schemas.entities import EntityGraphResponse

graph_router = APIRouter()


@graph_router.get(
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
    inv = await get_owned(uow, investigate_id, user)
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

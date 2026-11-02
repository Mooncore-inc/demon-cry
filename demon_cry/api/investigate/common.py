from fastapi import HTTPException

from demon_cry.database.models.entities import (
    InvestigateEntityLinkModel,
    InvestigateEntityModel,
)
from demon_cry.database.models.investigate import InvestigatesModel
from demon_cry.database.models.users import UserModel
from demon_cry.database.uow import AppUnitOfWork

CONTEXT_IDS_LIMIT = 100
GRAPH_NODE_LIMIT_DEFAULT = 500
GRAPH_EDGE_LIMIT = 5000
LINKS_LIST_LIMIT = 1000


async def get_owned(
    uow: AppUnitOfWork, investigate_id: int, user: UserModel
) -> InvestigatesModel:
    inv = await uow.investigates.get_by_id(investigate_id)
    if inv is None or inv.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return inv


async def get_entity(
    uow: AppUnitOfWork, investigate_id: int, entity_id: int
) -> InvestigateEntityModel:
    entity = await uow.entities.get_by_id(entity_id)
    if entity is None or entity.investigate_id != investigate_id:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


async def get_link(
    uow: AppUnitOfWork, investigate_id: int, link_id: int
) -> InvestigateEntityLinkModel:
    link = await uow.entity_links.get_by_id(link_id)
    if link is None or link.investigate_id != investigate_id:
        raise HTTPException(status_code=404, detail="Link not found")
    return link


def as_dict(value: object) -> dict:
    if isinstance(value, dict):
        return value
    return {"data": value}

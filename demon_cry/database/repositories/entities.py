from collections.abc import Sequence

from sqlalchemy import delete, or_, select

from demon_cry.database.models.entities import (
    InvestigateEntityLinkModel,
    InvestigateEntityModel,
)
from demon_cry.database.repositories.base import BaseRepository


class InvestigateEntitiesRepository(BaseRepository[InvestigateEntityModel]):
    model = InvestigateEntityModel

    async def get_all(
        self, limit: int = 100, offset: int = 0, **filters
    ) -> Sequence[InvestigateEntityModel]:
        stmt = (
            select(self.model)
            .filter_by(**filters)
            .order_by(self.model.id)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def search(
        self,
        investigate_id: int,
        limit: int = 100,
        offset: int = 0,
        type: str | None = None,
        types: Sequence[str] | None = None,
        search: str | None = None,
    ) -> Sequence[InvestigateEntityModel]:
        stmt = select(self.model).where(self.model.investigate_id == investigate_id)
        if type is not None:
            stmt = stmt.where(self.model.type == type)
        if types:
            stmt = stmt.where(self.model.type.in_(types))
        if search is not None:
            pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    self.model.value.ilike(pattern),
                    self.model.label.ilike(pattern),
                )
            )
        stmt = stmt.order_by(self.model.id).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete_by_investigation(self, investigate_id: int) -> None:
        await self.session.execute(
            delete(self.model).where(self.model.investigate_id == investigate_id)
        )


class InvestigateEntityLinksRepository(BaseRepository[InvestigateEntityLinkModel]):
    model = InvestigateEntityLinkModel

    async def get_all(
        self, limit: int = 100, offset: int = 0, **filters
    ) -> Sequence[InvestigateEntityLinkModel]:
        stmt = (
            select(self.model)
            .filter_by(**filters)
            .order_by(self.model.id)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_duplicate(
        self,
        investigate_id: int,
        source_id: int,
        target_id: int,
        relation: str,
        origin: str,
    ) -> InvestigateEntityLinkModel | None:
        stmt = select(self.model).where(
            self.model.investigate_id == investigate_id,
            self.model.source_id == source_id,
            self.model.target_id == target_id,
            self.model.relation == relation,
            self.model.origin == origin,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_edges_between(
        self,
        investigate_id: int,
        node_ids: set[int],
        limit: int = 5000,
        offset: int = 0,
    ) -> Sequence[InvestigateEntityLinkModel]:
        """Связи, у которых оба конца входят в `node_ids` (для /graph)."""
        stmt = (
            select(self.model)
            .where(
                self.model.investigate_id == investigate_id,
                self.model.source_id.in_(node_ids),
                self.model.target_id.in_(node_ids),
            )
            .order_by(self.model.id)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete_by_investigation(self, investigate_id: int) -> None:
        await self.session.execute(
            delete(self.model).where(self.model.investigate_id == investigate_id)
        )

    async def delete_for_entity(self, entity_id: int) -> None:
        """Удалить связи, где энтити source или target."""
        await self.session.execute(
            delete(self.model).where(
                or_(
                    self.model.source_id == entity_id,
                    self.model.target_id == entity_id,
                )
            )
        )

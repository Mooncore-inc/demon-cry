from collections.abc import Sequence

from sqlalchemy import delete, select

from demon_cry.database.models import InvestigatesDataModel, InvestigatesModel
from demon_cry.database.repositories.base import BaseRepository


class InvestigatesRepository(BaseRepository[InvestigatesModel]):
    model = InvestigatesModel

    async def get_all(
        self, limit: int = 100, offset: int = 0, **filters
    ) -> Sequence[InvestigatesModel]:
        stmt = (
            select(self.model)
            .filter_by(**filters)
            .order_by(self.model.id)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class InvestigatesDataRepository(BaseRepository[InvestigatesDataModel]):
    model = InvestigatesDataModel

    async def get_all(
        self, limit: int = 100, offset: int = 0, **filters
    ) -> Sequence[InvestigatesDataModel]:
        stmt = (
            select(self.model)
            .filter_by(**filters)
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

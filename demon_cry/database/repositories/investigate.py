from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from demon_cry.database.models import InvestigatesDataModel, InvestigatesModel
from demon_cry.database.repositories.base import BaseRepository


class InvestigatesRepository(BaseRepository[InvestigatesModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, InvestigatesModel)

    async def get_all(
        self, limit: int = 100, offset: int = 0, **filters
    ) -> Sequence[InvestigatesModel]:
        stmt = (
            select(InvestigatesModel)
            .filter_by(**filters)
            .order_by(InvestigatesModel.id)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class InvestigatesDataRepository(BaseRepository[InvestigatesDataModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, InvestigatesDataModel)

    async def get_all(
        self, limit: int = 100, offset: int = 0, **filters
    ) -> Sequence[InvestigatesDataModel]:
        stmt = (
            select(InvestigatesDataModel)
            .filter_by(**filters)
            .order_by(InvestigatesDataModel.id)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete_by_investigation(self, investigate_id: int) -> None:
        await self.session.execute(
            delete(InvestigatesDataModel).where(
                InvestigatesDataModel.investigate_id == investigate_id
            )
        )

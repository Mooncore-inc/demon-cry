from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends

from demon_cry.database.engine import async_session_factory
from demon_cry.database.uow import AppUnitOfWork


async def get_uow() -> AsyncGenerator[AppUnitOfWork, None]:
    async with async_session_factory() as session:
        uow = AppUnitOfWork(session)
        try:
            yield uow
        except BaseException:
            await uow.rollback()
            raise


UoWDep = Annotated[AppUnitOfWork, Depends(get_uow)]

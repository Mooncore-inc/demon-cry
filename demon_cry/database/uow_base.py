from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession


class UnitOfWorkBase:
    """Библиотечное ядро UoW: только sqlalchemy, без app/FastAPI импортов.

    Два режима:
    - `async with uow.transaction(): ...` — предпочтительно;
    - вручную `await uow.commit()` / `await uow.rollback()` — для сложной
      бизнес-логики, где выход из блока решает не всё.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._in_transaction = False

    async def commit(self) -> None:
        """Явно зафиксировать всё, что накоплено через репозитории."""
        await self.session.commit()

    async def rollback(self) -> None:
        """Явно откатить всё незакоммиченное."""
        await self.session.rollback()

    async def flush(self) -> None:
        await self.session.flush()

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator["UnitOfWorkBase", None]:
        if self._in_transaction:
            raise RuntimeError("Nested transactions are not supported")
        self._in_transaction = True
        try:
            yield self
        except BaseException:
            await self.rollback()
            raise
        else:
            await self.commit()
        finally:
            self._in_transaction = False

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from demon_cry.database.models.base import BaseModel
from demon_cry.database.uow import AppUnitOfWork


@pytest_asyncio.fixture
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
    yield async_sessionmaker(bind=engine, expire_on_commit=False)
    await engine.dispose()


@pytest.mark.asyncio
async def test_transaction_commit_persists(session_factory):
    async with session_factory() as session:
        uow = AppUnitOfWork(session)
        async with uow.transaction():
            user = await uow.users.create(username="alice", credentials="hash")

    async with session_factory() as session:
        uow = AppUnitOfWork(session)
        found = await uow.users.get(username="alice")
        assert found is not None
        assert found.id == user.id


@pytest.mark.asyncio
async def test_transaction_rollback_is_atomic(session_factory):
    async with session_factory() as session:
        uow = AppUnitOfWork(session)
        with pytest.raises(RuntimeError, match="boom"):
            async with uow.transaction():
                await uow.users.create(username="bob", credentials="h1")
                await uow.users.create(username="bobby", credentials="h2")
                raise RuntimeError("boom")

    async with session_factory() as session:
        uow = AppUnitOfWork(session)
        assert await uow.users.get(username="bob") is None
        assert await uow.users.get(username="bobby") is None


@pytest.mark.asyncio
async def test_write_without_transaction_is_not_persisted(session_factory):
    async with session_factory() as session:
        uow = AppUnitOfWork(session)
        await uow.users.create(username="carol", credentials="h")
        await uow.rollback()

    async with session_factory() as session:
        uow = AppUnitOfWork(session)
        assert await uow.users.get(username="carol") is None


@pytest.mark.asyncio
async def test_repositories_share_one_session(session_factory):
    async with session_factory() as session:
        uow = AppUnitOfWork(session)
        assert uow.users.session is session
        assert uow.settings.session is session
        assert uow.plugins.session is session
        assert uow.llms.session is session


@pytest.mark.asyncio
async def test_explicit_commit_persists_across_repos(session_factory):
    async with session_factory() as session:
        uow = AppUnitOfWork(session)
        await uow.users.create(username="dave", credentials="h")
        await uow.settings.create(key="theme", value="dark")
        await uow.commit()

    async with session_factory() as session:
        uow = AppUnitOfWork(session)
        assert await uow.users.get(username="dave") is not None
        assert await uow.settings.get(key="theme") is not None


@pytest.mark.asyncio
async def test_manual_rollback_on_business_error(session_factory):
    async with session_factory() as session:
        uow = AppUnitOfWork(session)
        try:
            await uow.users.create(username="frank", credentials="h")
            await uow.settings.create(key="theme", value="dark")
            raise ValueError("business fail")
            await uow.commit()
        except ValueError:
            await uow.rollback()

    async with session_factory() as session:
        uow = AppUnitOfWork(session)
        assert await uow.users.get(username="frank") is None
        assert await uow.settings.get(key="theme") is None

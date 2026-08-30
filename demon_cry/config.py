from dataclasses import dataclass

from sqlalchemy import select

from demon_cry.database.engine import async_session_factory
from demon_cry.database.models.settings import Settings

DEFAULTS: dict[str, str | int] = {
    "base_url": "CHANGEME",
    "master_key": "",
    "api_key": "",
    "model": "CHANGEME",
    "iteration_limit": 150,
    "server_host": "0.0.0.0",
    "server_port": 8000,
}

_numeric_keys = {k for k, v in DEFAULTS.items() if isinstance(v, int)}


@dataclass
class Config:
    base_url: str
    master_key: str
    api_key: str
    model: str
    iteration_limit: int
    server_host: str
    server_port: int

    @classmethod
    async def load(cls) -> "Config":
        async with async_session_factory() as session:
            result = await session.execute(select(Settings))
            rows = {s.key: s.value for s in result.scalars().all()}

        kwargs: dict[str, str | int] = {}
        for key, default in DEFAULTS.items():
            raw = rows.get(key)
            if raw is None:
                kwargs[key] = default
            elif key in _numeric_keys:
                kwargs[key] = int(raw)
            else:
                kwargs[key] = raw

        return cls(**kwargs)


async def init_defaults() -> None:
    async with async_session_factory() as session:
        result = await session.execute(select(Settings))
        if result.scalars().first() is not None:
            return
        for key, value in DEFAULTS.items():
            session.add(Settings(key=key, value=str(value)))
        await session.commit()


async def get_config_value(key: str) -> str | int:
    async with async_session_factory() as session:
        repo_result = await session.execute(
            select(Settings).where(Settings.key == key)
        )
        row = repo_result.scalar_one_or_none()
    if row is None:
        raise KeyError(f"Unknown config key: {key}")
    if key in _numeric_keys:
        return int(row.value)
    return row.value


async def set_config_value(key: str, value: str) -> None:
    if key not in DEFAULTS:
        raise KeyError(f"Unknown config key: {key}")
    async with async_session_factory() as session:
        result = await session.execute(
            select(Settings).where(Settings.key == key)
        )
        row = result.scalar_one_or_none()
        if row:
            row.value = value
        else:
            session.add(Settings(key=key, value=value))
        await session.commit()

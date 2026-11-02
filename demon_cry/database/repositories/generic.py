from collections.abc import Callable
from functools import partial
from typing import Self, cast, overload

from sqlalchemy.ext.asyncio import AsyncSession

from demon_cry.database.models.base import BaseModel
from demon_cry.database.repositories.base import BaseRepository
from demon_cry.database.uow_base import UnitOfWorkBase


def _default_repository[M: BaseModel](
    model: type[M], session: AsyncSession
) -> BaseRepository[M]:
    """Типовой репозиторий: BaseRepository, привязанный к модели."""
    repository: BaseRepository[M] = BaseRepository(session)
    repository.model = model
    return repository


class _Repo[G]:
    """Лениво создаёт репозиторий на сессии UoW при первом обращении.

    Кэширует в `__dict__` экземпляра UoW, поэтому `uow.users is uow.users`.
    """

    def __init__(self, factory: Callable[[AsyncSession], G]) -> None:
        self.factory = factory

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    @overload
    def __get__(self, instance: None, owner: type) -> Self: ...

    @overload
    def __get__(self, instance: UnitOfWorkBase, owner: type) -> G: ...

    def __get__(self, instance: UnitOfWorkBase | None, owner: type) -> Self | G:
        if instance is None:
            return self
        cached = instance.__dict__.get(self.name)
        if cached is None:
            cached = self.factory(instance.session)
            instance.__dict__[self.name] = cached
        return cached


@overload
def repo[R: BaseRepository](source: type[R]) -> _Repo[R]:
    """Кастомный класс репозитория - подключается как есть."""


@overload
def repo[M: BaseModel](source: type[M]) -> _Repo[BaseRepository[M]]:
    """Модель - для неё генерируется типовой репозиторий."""


def repo[M: BaseModel, R: BaseRepository](
    source: type[R] | type[M],
) -> _Repo[R] | _Repo[BaseRepository[M]]:
    """Декларативное подключение репозитория к UoW.

    Принимает либо модель `BaseModel` (будет сгенерирован типовой
    репозиторий без кастомной логики), либо класс `BaseRepository`
    (с кастомной логикой), например `investigates = repo(InvestigatesRepository)`.
    """
    if isinstance(source, type) and issubclass(source, BaseRepository):
        repository = cast("type[R]", source)
        return _Repo[R](repository)
    model = cast("type[M]", source)
    return _Repo[BaseRepository[M]](partial(_default_repository, model))

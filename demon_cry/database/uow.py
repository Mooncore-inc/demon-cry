from demon_cry.database.models import (
    LLMModel,
    PluginModel,
    SettingsModel,
    UserModel,
)
from demon_cry.database.repositories import (
    InvestigateEntitiesRepository,
    InvestigateEntityLinksRepository,
    InvestigatesDataRepository,
    InvestigatesRepository,
    repo,
)
from demon_cry.database.uow_base import UnitOfWorkBase


class AppUnitOfWork(UnitOfWorkBase):
    """App-обвязка: репозитории подключаются декларативно и лениво.

    Новая сущность - одна строка:
    - `name = repo(Model)` - типовой репозиторий сгенерируется сам;
    - `name = repo(CustomRepo)` - класс с кастомной логикой, как есть.
    """

    users = repo(UserModel)
    settings = repo(SettingsModel)
    plugins = repo(PluginModel)
    llms = repo(LLMModel)
    investigates = repo(InvestigatesRepository)
    investigates_data = repo(InvestigatesDataRepository)
    entities = repo(InvestigateEntitiesRepository)
    entity_links = repo(InvestigateEntityLinksRepository)

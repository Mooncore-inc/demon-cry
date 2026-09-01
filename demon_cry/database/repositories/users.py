from sqlalchemy.ext.asyncio import AsyncSession

from demon_cry.database.models import UserModel
from demon_cry.database.repositories import BaseRepository


class UserRepository(BaseRepository[UserModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserModel)

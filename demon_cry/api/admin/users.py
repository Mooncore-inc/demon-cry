from fastapi import APIRouter, Depends, Query

from demon_cry.api.dependencies import get_user_repo
from demon_cry.database.repositories.users import UserRepository

users_router = APIRouter(prefix="/users")

@users_router.get("/{user_id}")
async def get_user(user_id: int, user_repo: UserRepository = Depends(get_user_repo)):
    user = await user_repo.get(id=user_id)
    return user

@users_router.delete("/{user_id}")
async def delete_user(user_id: int, user_repo: UserRepository = Depends(get_user_repo)):
    user = await user_repo.get(id=user_id)
    if user:
        return await user_repo.delete(user)

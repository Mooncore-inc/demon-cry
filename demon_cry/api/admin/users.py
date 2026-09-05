from fastapi import APIRouter, Depends, Query

from demon_cry.api.dependencies import UserRepo

users_router = APIRouter(prefix="/users")

@users_router.get("/{user_id}")
async def get_user(user_id: int, user_repo: UserRepo):
    user = await user_repo.get(id=user_id)
    return user

@users_router.delete("/{user_id}")
async def delete_user(user_id: int, user_repo: UserRepo):
    user = await user_repo.get(id=user_id)
    if user:
        return await user_repo.delete(user)

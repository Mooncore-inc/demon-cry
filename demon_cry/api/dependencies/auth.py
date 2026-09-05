from typing import Annotated
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from demon_cry.database.models.users import UserModel
from demon_cry.api.dependencies.database import UserRepo

security = HTTPBearer(auto_error=False)


async def get_current_user(
    user_repo: UserRepo,
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> UserModel:
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing API key")

    user = await user_repo.get(credentials=credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return user

CurrentUser = Annotated[UserModel, Depends(get_current_user)]

async def require_admin(user: CurrentUser) -> UserModel:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

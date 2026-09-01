from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from demon_cry.database.models.users import UserModel
from demon_cry.api.dependencies import get_user_repo
from demon_cry.database.repositories.users import UserRepository

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    user_repo: UserRepository = Depends(get_user_repo),
) -> UserModel:
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing API key")

    user = await user_repo.get(credentials=credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return user

async def require_admin(user: UserModel = Depends(get_current_user)) -> UserModel:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

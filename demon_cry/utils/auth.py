from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from demon_cry.config import Config
from demon_cry.utils.dependencies import get_config

security = HTTPBearer(auto_error=False)

async def verify_master_key(
    credentials: HTTPAuthorizationCredentials = Security(security),
    config: Config = Depends(get_config),
):
    if not config.master_key:
        return

    if not credentials or credentials.credentials != config.master_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

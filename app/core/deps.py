from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.errors import BakerProfitError
from app.db.session import get_db
from app.models.user import User

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    from app.services.auth_service import get_current_user as _get
    try:
        return _get(db, credentials.credentials)
    except BakerProfitError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.to_dict())


def require_roles(*roles: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail={"error": {"code": "FORBIDDEN", "message": "Insufficient permissions"}})
        return user
    return checker

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.errors import BakerProfitError
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, MeResponse, MeUpdateRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    try:
        _user, tokens = auth_service.register(db, data)
        return tokens
    except BakerProfitError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.to_dict())


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    try:
        _user, tokens = auth_service.login(db, data)
        return tokens
    except BakerProfitError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.to_dict())


@router.post("/refresh", response_model=TokenResponse)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    try:
        return auth_service.refresh(db, data.refresh_token)
    except BakerProfitError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.to_dict())


@router.get("/me", response_model=MeResponse)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models.tenant import Tenant
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    return {
        "id": user.id,
        "tenant_id": user.tenant_id,
        "tenant_name": tenant.name if tenant else "",
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
    }


@router.patch("/me", response_model=MeResponse)
def update_me(data: MeUpdateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models.tenant import Tenant
    user.full_name = data.full_name.strip()
    db.commit()
    db.refresh(user)
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    return {
        "id": user.id,
        "tenant_id": user.tenant_id,
        "tenant_name": tenant.name if tenant else "",
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
    }

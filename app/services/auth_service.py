import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.errors import BakerProfitError
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse


def register(db: Session, data: RegisterRequest) -> tuple[User, TokenResponse]:
    if db.query(User).filter(User.email == data.email).first():
        raise BakerProfitError("EMAIL_TAKEN", "An account with this email already exists.", status_code=409)

    # Create tenant (bakery)
    slug = data.bakery_name.lower().replace(" ", "-")[:100]
    tenant = Tenant(name=data.bakery_name, slug=_unique_slug(db, slug))
    db.add(tenant)
    db.flush()

    user = User(
        tenant_id=tenant.id,
        full_name=data.full_name,
        email=data.email,
        password_hash=hash_password(data.password),
        role="owner",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    tokens = _issue_tokens(str(user.id), str(tenant.id))
    return user, tokens


def login(db: Session, data: LoginRequest) -> tuple[User, TokenResponse]:
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise BakerProfitError("INVALID_CREDENTIALS", "Invalid email or password.", status_code=401)
    if not user.is_active:
        raise BakerProfitError("ACCOUNT_DISABLED", "This account is disabled.", status_code=403)

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    tokens = _issue_tokens(str(user.id), str(user.tenant_id))
    return user, tokens


def refresh(db: Session, refresh_token: str) -> TokenResponse:
    try:
        payload = decode_token(refresh_token)
    except ValueError:
        raise BakerProfitError("INVALID_TOKEN", "Refresh token is invalid or expired.", status_code=401)

    if payload.get("type") != "refresh":
        raise BakerProfitError("INVALID_TOKEN", "Not a refresh token.", status_code=401)

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
    if not user or not user.is_active:
        raise BakerProfitError("INVALID_TOKEN", "User not found or disabled.", status_code=401)

    return _issue_tokens(str(user.id), str(user.tenant_id))


def get_current_user(db: Session, token: str) -> User:
    try:
        payload = decode_token(token)
    except ValueError:
        raise BakerProfitError("INVALID_TOKEN", "Token is invalid or expired.", status_code=401)

    if payload.get("type") != "access":
        raise BakerProfitError("INVALID_TOKEN", "Not an access token.", status_code=401)

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
    if not user or not user.is_active:
        raise BakerProfitError("INVALID_TOKEN", "User not found.", status_code=401)
    return user


def _issue_tokens(user_id: str, tenant_id: str) -> TokenResponse:
    access = create_access_token(user_id, {"tenant_id": tenant_id})
    refresh = create_refresh_token(user_id)
    return TokenResponse(access_token=access, refresh_token=refresh)


def _unique_slug(db: Session, base: str) -> str:
    slug = base
    counter = 1
    while db.query(Tenant).filter(Tenant.slug == slug).first():
        slug = f"{base}-{counter}"
        counter += 1
    return slug

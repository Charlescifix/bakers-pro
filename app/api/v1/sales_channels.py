import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.errors import BakerProfitError
from app.db.session import get_db
from app.models.user import User
from app.schemas.sales_channel import SalesChannelCreate, SalesChannelResponse, SalesChannelUpdate
from app.services import sales_channel_service

router = APIRouter(prefix="/sales-channels", tags=["sales-channels"])


def _err(exc: Exception) -> HTTPException:
    code = getattr(exc, "status_code", 400)
    return HTTPException(status_code=code, detail=exc.to_dict() if hasattr(exc, "to_dict") else str(exc))


@router.get("", response_model=list[SalesChannelResponse])
def list_channels(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return sales_channel_service.list_channels(db, user.tenant_id)


@router.post("", response_model=SalesChannelResponse, status_code=201)
def create_channel(data: SalesChannelCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return sales_channel_service.create_channel(db, user.tenant_id, data)


@router.patch("/{channel_id}", response_model=SalesChannelResponse)
def update_channel(channel_id: uuid.UUID, data: SalesChannelUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return sales_channel_service.update_channel(db, user.tenant_id, channel_id, data)
    except BakerProfitError as exc:
        raise _err(exc)

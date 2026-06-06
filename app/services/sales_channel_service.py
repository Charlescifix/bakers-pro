import uuid

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.sales_channel import SalesChannel
from app.schemas.sales_channel import SalesChannelCreate, SalesChannelUpdate


def create_channel(db: Session, tenant_id: uuid.UUID, data: SalesChannelCreate) -> SalesChannel:
    obj = SalesChannel(tenant_id=tenant_id, **data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_channel(db: Session, tenant_id: uuid.UUID, channel_id: uuid.UUID) -> SalesChannel:
    obj = db.query(SalesChannel).filter(
        SalesChannel.id == channel_id, SalesChannel.tenant_id == tenant_id
    ).first()
    if not obj:
        raise NotFoundError("SalesChannel", str(channel_id))
    return obj


def list_channels(db: Session, tenant_id: uuid.UUID) -> list[SalesChannel]:
    return (
        db.query(SalesChannel)
        .filter(SalesChannel.tenant_id == tenant_id, SalesChannel.is_active == True)
        .order_by(SalesChannel.name)
        .all()
    )


def update_channel(
    db: Session, tenant_id: uuid.UUID, channel_id: uuid.UUID, data: SalesChannelUpdate
) -> SalesChannel:
    obj = get_channel(db, tenant_id, channel_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj

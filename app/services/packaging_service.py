import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.calculators.cost_engine import unit_cost as calc_unit_cost
from app.core.errors import NotFoundError
from app.core.units import convert_to_base
from app.models.packaging import PackagingItem
from app.schemas.packaging import PackagingCreate, PackagingUpdate


def _compute_unit_cost(price: Decimal, qty: Decimal, unit_code: str) -> Decimal:
    qty_base = convert_to_base(qty, unit_code)
    return calc_unit_cost(price, qty_base)


def create_packaging(db: Session, tenant_id: uuid.UUID, data: PackagingCreate) -> PackagingItem:
    unit_cost = _compute_unit_cost(
        data.purchase_price, data.purchase_quantity, data.purchase_unit_code
    )
    item = PackagingItem(
        tenant_id=tenant_id,
        name=data.name,
        supplier_id=data.supplier_id,
        purchase_price=data.purchase_price,
        purchase_quantity=data.purchase_quantity,
        purchase_unit_code=data.purchase_unit_code,
        unit_cost=unit_cost,
        reorder_level=data.reorder_level,
        notes=data.notes,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_packaging(db: Session, tenant_id: uuid.UUID, item_id: uuid.UUID) -> PackagingItem:
    obj = db.query(PackagingItem).filter(
        PackagingItem.id == item_id, PackagingItem.tenant_id == tenant_id
    ).first()
    if not obj:
        raise NotFoundError("PackagingItem", str(item_id))
    return obj


def list_packaging(db: Session, tenant_id: uuid.UUID, active_only: bool = True) -> list[PackagingItem]:
    q = db.query(PackagingItem).filter(PackagingItem.tenant_id == tenant_id)
    if active_only:
        q = q.filter(PackagingItem.is_active == True)
    return q.order_by(PackagingItem.name).all()


def update_packaging(
    db: Session, tenant_id: uuid.UUID, item_id: uuid.UUID, data: PackagingUpdate
) -> PackagingItem:
    obj = get_packaging(db, tenant_id, item_id)
    changed_price = False
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(obj, field, value)
        if field in ("purchase_price", "purchase_quantity", "purchase_unit_code"):
            changed_price = True
    if changed_price:
        obj.unit_cost = _compute_unit_cost(
            obj.purchase_price, obj.purchase_quantity, obj.purchase_unit_code
        )
    db.commit()
    db.refresh(obj)
    return obj


def delete_packaging(db: Session, tenant_id: uuid.UUID, item_id: uuid.UUID) -> None:
    obj = get_packaging(db, tenant_id, item_id)
    obj.is_active = False
    db.commit()

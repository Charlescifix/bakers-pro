import uuid

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate, SupplierUpdate


def create_supplier(db: Session, tenant_id: uuid.UUID, data: SupplierCreate) -> Supplier:
    obj = Supplier(tenant_id=tenant_id, **data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_supplier(db: Session, tenant_id: uuid.UUID, supplier_id: uuid.UUID) -> Supplier:
    obj = db.query(Supplier).filter(
        Supplier.id == supplier_id, Supplier.tenant_id == tenant_id
    ).first()
    if not obj:
        raise NotFoundError("Supplier", str(supplier_id))
    return obj


def list_suppliers(db: Session, tenant_id: uuid.UUID) -> list[Supplier]:
    return (
        db.query(Supplier)
        .filter(Supplier.tenant_id == tenant_id, Supplier.is_active == True)
        .order_by(Supplier.name)
        .all()
    )


def update_supplier(
    db: Session, tenant_id: uuid.UUID, supplier_id: uuid.UUID, data: SupplierUpdate
) -> Supplier:
    obj = get_supplier(db, tenant_id, supplier_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_supplier(db: Session, tenant_id: uuid.UUID, supplier_id: uuid.UUID) -> None:
    obj = get_supplier(db, tenant_id, supplier_id)
    obj.is_active = False
    db.commit()

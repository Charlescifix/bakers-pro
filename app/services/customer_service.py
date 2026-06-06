import uuid

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate


def create_customer(db: Session, tenant_id: uuid.UUID, data: CustomerCreate) -> Customer:
    obj = Customer(tenant_id=tenant_id, **data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_customer(db: Session, tenant_id: uuid.UUID, customer_id: uuid.UUID) -> Customer:
    obj = db.query(Customer).filter(
        Customer.id == customer_id, Customer.tenant_id == tenant_id
    ).first()
    if not obj:
        raise NotFoundError("Customer", str(customer_id))
    return obj


def list_customers(db: Session, tenant_id: uuid.UUID, active_only: bool = True) -> list[Customer]:
    q = db.query(Customer).filter(Customer.tenant_id == tenant_id)
    if active_only:
        q = q.filter(Customer.is_active == True)
    return q.order_by(Customer.full_name).all()


def update_customer(
    db: Session, tenant_id: uuid.UUID, customer_id: uuid.UUID, data: CustomerUpdate
) -> Customer:
    obj = get_customer(db, tenant_id, customer_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj

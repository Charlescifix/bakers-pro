import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.core.errors import BakerProfitError
from app.db.session import get_db
from app.models.label import Label
from app.models.user import User
from app.schemas.label import GenerateLabelRequest, LabelDataOut, LabelOut
from app.services.label_service import generate_label

router = APIRouter(prefix="/labels", tags=["labels"])


def _err(exc):
    from fastapi import HTTPException
    code = getattr(exc, "status_code", 400)
    return HTTPException(status_code=code, detail=exc.to_dict() if hasattr(exc, "to_dict") else str(exc))


@router.post("/generate-allergen-label", response_model=LabelDataOut, status_code=201)
def generate_allergen_label(
    payload: GenerateLabelRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("owner", "manager")),
):
    payload.label_type = "allergen"
    try:
        result = generate_label(db, user.tenant_id, payload)
        db.commit()
        return result
    except BakerProfitError as exc:
        raise _err(exc)


@router.post("/generate-ingredient-label", response_model=LabelDataOut, status_code=201)
def generate_ingredient_label(
    payload: GenerateLabelRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("owner", "manager")),
):
    payload.label_type = "ingredient"
    try:
        result = generate_label(db, user.tenant_id, payload)
        db.commit()
        return result
    except BakerProfitError as exc:
        raise _err(exc)


@router.post("/generate", response_model=LabelDataOut, status_code=201)
def generate_any_label(
    payload: GenerateLabelRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("owner", "manager")),
):
    try:
        result = generate_label(db, user.tenant_id, payload)
        db.commit()
        return result
    except BakerProfitError as exc:
        raise _err(exc)


@router.get("/variant/{variant_id}", response_model=list[LabelOut])
def list_labels_for_variant(
    variant_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return (
        db.query(Label)
        .filter(Label.product_variant_id == variant_id, Label.tenant_id == user.tenant_id)
        .all()
    )

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.core.errors import BakerProfitError
from app.db.session import get_db
from app.models.allergen import Allergen, IngredientAllergen
from app.models.ingredient import Ingredient
from app.models.user import User
from app.schemas.allergen import (
    AllergenMatrixOut,
    AllergenOut,
    IngredientAllergenCreate,
    IngredientAllergenOut,
)
from app.services.label_service import get_allergen_matrix, seed_allergens

router = APIRouter(prefix="/allergens", tags=["allergens"])


@router.get("", response_model=list[AllergenOut])
def list_allergens(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return db.query(Allergen).order_by(Allergen.name).all()


@router.post("/seed", status_code=201)
def seed(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("owner")),
):
    count = seed_allergens(db)
    db.commit()
    return {"seeded": count}


@router.get("/matrix", response_model=AllergenMatrixOut)
def allergen_matrix(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return get_allergen_matrix(db, user.tenant_id)


@router.get("/ingredients/{ingredient_id}", response_model=list[IngredientAllergenOut])
def list_ingredient_allergens(
    ingredient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ing = db.query(Ingredient).filter(
        Ingredient.id == ingredient_id,
        Ingredient.tenant_id == user.tenant_id,
    ).first()
    if not ing:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return db.query(IngredientAllergen).filter(IngredientAllergen.ingredient_id == ingredient_id).all()


@router.post("/ingredients/{ingredient_id}", response_model=IngredientAllergenOut, status_code=201)
def add_ingredient_allergen(
    ingredient_id: uuid.UUID,
    payload: IngredientAllergenCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("owner", "manager")),
):
    ing = db.query(Ingredient).filter(
        Ingredient.id == ingredient_id,
        Ingredient.tenant_id == user.tenant_id,
    ).first()
    if not ing:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    allergen = db.query(Allergen).filter(Allergen.id == payload.allergen_id).first()
    if not allergen:
        raise HTTPException(status_code=404, detail="Allergen not found")

    existing = db.query(IngredientAllergen).filter(
        IngredientAllergen.ingredient_id == ingredient_id,
        IngredientAllergen.allergen_id == payload.allergen_id,
    ).first()
    if existing:
        existing.contains_status = payload.contains_status
        existing.notes = payload.notes
        db.commit()
        db.refresh(existing)
        return existing

    link = IngredientAllergen(
        ingredient_id=ingredient_id,
        allergen_id=payload.allergen_id,
        contains_status=payload.contains_status,
        notes=payload.notes,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


@router.delete("/ingredients/{ingredient_id}/{allergen_id}", status_code=204)
def remove_ingredient_allergen(
    ingredient_id: uuid.UUID,
    allergen_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("owner", "manager")),
):
    ing = db.query(Ingredient).filter(
        Ingredient.id == ingredient_id,
        Ingredient.tenant_id == user.tenant_id,
    ).first()
    if not ing:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    link = db.query(IngredientAllergen).filter(
        IngredientAllergen.ingredient_id == ingredient_id,
        IngredientAllergen.allergen_id == allergen_id,
    ).first()
    if link:
        db.delete(link)
        db.commit()

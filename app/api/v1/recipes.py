import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.errors import BakerProfitError
from app.db.session import get_db
from app.models.user import User
from app.schemas.recipe import (
    CostPreviewResponse,
    PackagingRuleCreate,
    PackagingRuleResponse,
    RecipeCreate,
    RecipeResponse,
    RecipeUpdate,
    RecipeVersionCreate,
    RecipeVersionResponse,
    RecipeWithVersionResponse,
    ScaleRequest,
)
from app.services import recipe_service

router = APIRouter(prefix="/recipes", tags=["recipes"])


def _err(exc: Exception) -> HTTPException:
    code = getattr(exc, "status_code", 400)
    detail = exc.to_dict() if hasattr(exc, "to_dict") else str(exc)
    return HTTPException(status_code=code, detail=detail)


@router.get("", response_model=list[RecipeResponse])
def list_recipes(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return recipe_service.list_recipes(db, user.tenant_id)


@router.post("", response_model=RecipeWithVersionResponse, status_code=201)
def create_recipe(
    data: RecipeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        recipe = recipe_service.create_recipe(db, user.tenant_id, user.id, data)
        active_version = recipe_service._get_active_version(db, recipe)
        result = RecipeWithVersionResponse.model_validate(recipe)
        if active_version:
            result.active_version = RecipeVersionResponse.model_validate(active_version)
        return result
    except (BakerProfitError, ValueError) as exc:
        raise _err(exc)


@router.get("/{recipe_id}", response_model=RecipeWithVersionResponse)
def get_recipe(
    recipe_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        recipe = recipe_service.get_recipe(db, user.tenant_id, recipe_id)
        active_version = recipe_service._get_active_version(db, recipe)
        result = RecipeWithVersionResponse.model_validate(recipe)
        if active_version:
            result.active_version = RecipeVersionResponse.model_validate(active_version)
        return result
    except BakerProfitError as exc:
        raise _err(exc)


@router.patch("/{recipe_id}", response_model=RecipeResponse)
def update_recipe(
    recipe_id: uuid.UUID,
    data: RecipeUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return recipe_service.update_recipe(db, user.tenant_id, recipe_id, data)
    except (BakerProfitError, ValueError) as exc:
        raise _err(exc)


@router.delete("/{recipe_id}", status_code=204)
def delete_recipe(
    recipe_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        recipe_service.delete_recipe(db, user.tenant_id, recipe_id)
    except BakerProfitError as exc:
        raise _err(exc)


@router.post("/{recipe_id}/versions", response_model=RecipeVersionResponse, status_code=201)
def create_version(
    recipe_id: uuid.UUID,
    data: RecipeVersionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return recipe_service.create_version(db, user.tenant_id, recipe_id, user.id, data)
    except (BakerProfitError, ValueError) as exc:
        raise _err(exc)


@router.post("/{recipe_id}/versions/{version_id}/activate", response_model=RecipeVersionResponse)
def activate_version(
    recipe_id: uuid.UUID,
    version_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return recipe_service.activate_version(db, user.tenant_id, recipe_id, version_id)
    except BakerProfitError as exc:
        raise _err(exc)


@router.get("/{recipe_id}/cost-preview", response_model=CostPreviewResponse)
def cost_preview(
    recipe_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        result = recipe_service.cost_preview(db, user.tenant_id, recipe_id)
        return CostPreviewResponse(
            recipe_id=result.recipe_id,
            recipe_name=result.recipe_name,
            version_id=result.version_id,
            version_number=result.version_number,
            base_yield_quantity=result.base_yield_quantity,
            base_yield_unit=result.base_yield_unit,
            ingredient_lines=[
                {
                    "ingredient_id": l.ingredient_id,
                    "ingredient_name": l.ingredient_name,
                    "quantity_used": l.quantity_used,
                    "unit_code": l.unit_code,
                    "quantity_in_base": l.quantity_in_base,
                    "unit_cost_base": l.unit_cost_base,
                    "waste_percent": l.waste_percent,
                    "line_cost": l.line_cost,
                }
                for l in result.ingredient_lines
            ],
            packaging_lines=[
                {
                    "packaging_item_id": l.packaging_item_id,
                    "packaging_item_name": l.packaging_item_name,
                    "rule_type": l.rule_type,
                    "quantity": l.quantity,
                    "unit_cost": l.unit_cost,
                    "line_cost": l.line_cost,
                }
                for l in result.packaging_lines
            ],
            total_ingredient_cost=result.total_ingredient_cost,
            total_packaging_cost=result.total_packaging_cost,
            labour_minutes=result.labour_minutes,
            hourly_rate=result.hourly_rate,
            total_labour_cost=result.total_labour_cost,
            total_cost_excluding_labour=result.total_cost_excluding_labour,
            total_cost_including_labour=result.total_cost_including_labour,
            cost_per_item_excl_labour=result.cost_per_item_excl_labour,
            cost_per_item_incl_labour=result.cost_per_item_incl_labour,
            recommended_prices=result.recommended_prices,
        )
    except (BakerProfitError, ValueError) as exc:
        raise _err(exc)


@router.post("/{recipe_id}/scale")
def scale_recipe(
    recipe_id: uuid.UUID,
    data: ScaleRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return recipe_service.scale(db, user.tenant_id, recipe_id, data.order_quantity)
    except (BakerProfitError, ValueError) as exc:
        raise _err(exc)


@router.post("/{recipe_id}/packaging-rules", response_model=PackagingRuleResponse, status_code=201)
def add_packaging_rule(
    recipe_id: uuid.UUID,
    data: PackagingRuleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return recipe_service.add_packaging_rule(db, user.tenant_id, recipe_id, data)
    except (BakerProfitError, ValueError) as exc:
        raise _err(exc)

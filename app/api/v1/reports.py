from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.reports import ChannelProfitabilityRow, DashboardOut, ProductProfitabilityRow, WeeklyReportOut
from app.services import reporting_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return reporting_service.get_dashboard(db, user.tenant_id)


@router.get("/weekly", response_model=WeeklyReportOut)
def weekly(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return reporting_service.get_weekly_report(db, user.tenant_id)


@router.get("/monthly", response_model=WeeklyReportOut)
def monthly(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return reporting_service.get_monthly_report(db, user.tenant_id)


@router.get("/product-profitability", response_model=list[ProductProfitabilityRow])
def product_profitability(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return reporting_service.get_product_profitability(db, user.tenant_id)


@router.get("/channel-profitability", response_model=list[ChannelProfitabilityRow])
def channel_profitability(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return reporting_service.get_channel_profitability(db, user.tenant_id)

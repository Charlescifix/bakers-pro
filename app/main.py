from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import (
    allergens, auth, compliance, customers, imports, ingredients, intelligence,
    labels, orders, packaging, production, products, quotes, recipes, reports,
    sales_channels, shopping_lists, suppliers,
)
from app.core.config import settings
from app.core.errors import BakerProfitError

app = FastAPI(
    title="BakerProfit OS",
    description="Pricing, profit, and order planner for small bakers.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(BakerProfitError)
async def baker_profit_error_handler(request: Request, exc: BakerProfitError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())


API_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(suppliers.router, prefix=API_PREFIX)
app.include_router(ingredients.router, prefix=API_PREFIX)
app.include_router(packaging.router, prefix=API_PREFIX)
app.include_router(recipes.router, prefix=API_PREFIX)
app.include_router(products.router, prefix=API_PREFIX)
app.include_router(customers.router, prefix=API_PREFIX)
app.include_router(sales_channels.router, prefix=API_PREFIX)
app.include_router(quotes.router, prefix=API_PREFIX)
app.include_router(orders.router, prefix=API_PREFIX)
app.include_router(production.router, prefix=API_PREFIX)
app.include_router(shopping_lists.router, prefix=API_PREFIX)
app.include_router(imports.router, prefix=API_PREFIX)
app.include_router(reports.router, prefix=API_PREFIX)
app.include_router(intelligence.router, prefix=API_PREFIX)
app.include_router(allergens.router, prefix=API_PREFIX)
app.include_router(labels.router, prefix=API_PREFIX)
app.include_router(compliance.router, prefix=API_PREFIX)


@app.get("/health")
def health():
    return {"status": "ok", "service": "BakerProfit OS"}

from fastapi import APIRouter, Request

from app.api import preview

router = APIRouter(prefix="/api/orders", tags=["订单采集"])


@router.get("/{source}")
def inspect(request: Request, source: str):
    return preview(request, source)["orders"]

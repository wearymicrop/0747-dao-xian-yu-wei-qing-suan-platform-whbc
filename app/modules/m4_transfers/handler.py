from fastapi import APIRouter, Request

from app.api import preview

router = APIRouter(prefix="/api/transfers", tags=["换票链路"])


@router.get("/{source}")
def inspect(request: Request, source: str):
    return preview(request, source)["transfers"]

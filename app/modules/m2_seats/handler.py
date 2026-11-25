from fastapi import APIRouter, Request

from app.api import preview

router = APIRouter(prefix="/api/seats", tags=["席位层级"])


@router.get("/{source}")
def inspect(request: Request, source: str):
    return preview(request, source)["seats"]

from fastapi import APIRouter, Request

from app.api import preview

router = APIRouter(prefix="/api/waitlist", tags=["候补递补"])


@router.get("/{source}")
def inspect(request: Request, source: str):
    return preview(request, source)["waitlist"]

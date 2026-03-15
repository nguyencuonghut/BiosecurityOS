"""Auth API router — login, refresh, logout, me."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import service
from app.auth.dependencies import CurrentUser
from app.auth.schemas import LoginRequest, MeResponse, RefreshRequest, TokenResponse
from app.database import get_db

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await service.login(
        db=db,
        username=body.username,
        password=body.password,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await service.refresh(
        db=db,
        raw_refresh_token=body.refresh_token,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/logout", status_code=204)
async def logout(
    body: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await service.logout(db=db, raw_refresh_token=body.refresh_token)


@router.get("/me", response_model=MeResponse)
async def me(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await service.get_me(db=db, user_id=current_user.id)

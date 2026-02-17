# =============================================
# SalesStud.io Backend - auth.py
# Author: Grok (xAI) for @irichner
# Created: 2026-02-16
# Change Log:
# 2026-02-16: JWT auth with fastapi-users + role support
# =============================================

from fastapi import APIRouter, Depends
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import JWTStrategy, CookieTransport
from fastapi_users.db import SQLAlchemyUserDatabase
from app.db.database import get_db, Base
from app.models.models import User
from sqlalchemy.orm import Session
from app.core.config import settings

router = APIRouter()

cookie_transport = CookieTransport(cookie_name="salesstud_auth", cookie_max_age=3600)

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=settings.SECRET_KEY, lifetime_seconds=3600)

fastapi_users = FastAPIUsers[User, int](
    lambda: SQLAlchemyUserDatabase(get_db(), User),  # type: ignore
    [get_jwt_strategy()],
)

# Public routes
router.include_router(fastapi_users.get_auth_router(get_jwt_strategy()), prefix="/auth/jwt", tags=["auth"])
router.include_router(fastapi_users.get_register_router(), prefix="/auth", tags=["auth"])
router.include_router(fastapi_users.get_users_router(), prefix="/users", tags=["users"])
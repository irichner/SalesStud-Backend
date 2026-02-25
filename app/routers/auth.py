# =============================================
# SalesStud.io Backend - auth.py
# Author: Grok (xAI) for @irichner
# Created: 2026-02-16
# Change Log:
# 2026-02-16: JWT auth with fastapi-users + role support
# =============================================

from fastapi import APIRouter, Depends, HTTPException
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import JWTStrategy, CookieTransport, AuthenticationBackend
from fastapi_users.db import SQLAlchemyUserDatabase
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import User, UserPreferences
from app.core.config import settings

router = APIRouter()

# Pydantic schemas for user creation and update
class UserCreate(BaseModel):
    username: str
    full_name: str
    email: str
    password: str
    role: str = "SalesRep"
    is_active: bool = True

class UserUpdate(BaseModel):
    username: str | None = None
    full_name: str | None = None
    email: str | None = None
    password: str | None = None
    role: str | None = None
    is_active: bool | None = None

class UserRead(BaseModel):
    id: int
    username: str
    full_name: str
    email: str
    role: str
    is_active: bool
    auth_provider: str
    created_date: str
    updated_date: str

    class Config:
        from_attributes = True

# Authentication setup
cookie_transport = CookieTransport(cookie_name="salesstud_auth", cookie_max_age=3600)

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=settings.SECRET_KEY, lifetime_seconds=3600)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, int](
    lambda: SQLAlchemyUserDatabase(get_db(), User),
    [auth_backend],
)

# Public routes
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"]
)
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"]
)
router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"]
)

# Current user endpoint
@router.get("/me", response_model=UserRead)
async def get_current_user(user: User = Depends(fastapi_users.current_user())):
    return UserRead.from_orm(user)

# User preferences endpoints
class UserPreferencesUpdate(BaseModel):
    saved_tabs: list | None = None

@router.get("/preferences")
async def get_user_preferences(
    user: User = Depends(fastapi_users.current_user()),
    db: Session = Depends(get_db)
):
    """Get user preferences"""
    prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user.id).first()
    if not prefs:
        return {"saved_tabs": None}
    return {"saved_tabs": prefs.saved_tabs}

@router.post("/preferences")
async def save_user_preferences(
    prefs: UserPreferencesUpdate,
    user: User = Depends(fastapi_users.current_user()),
    db: Session = Depends(get_db)
):
    """Save user preferences"""
    existing_prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user.id).first()
    if existing_prefs:
        existing_prefs.saved_tabs = prefs.saved_tabs
        db.commit()
    else:
        new_prefs = UserPreferences(user_id=user.id, saved_tabs=prefs.saved_tabs)
        db.add(new_prefs)
        db.commit()
    return {"message": "Preferences saved successfully"}

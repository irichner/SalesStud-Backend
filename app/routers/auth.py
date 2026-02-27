# =============================================
# SalesStud.io Backend - auth.py
# Author: Grok (xAI) for @irichner
# Created: 2026-02-16
# Change Log:
# 2026-02-16: JWT auth with fastapi-users + role support
# =============================================

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import JWTStrategy, CookieTransport, AuthenticationBackend
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.manager import BaseUserManager
from typing import Optional
from httpx_oauth.clients.google import GoogleOAuth2
import httpx
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

class CustomUserManager(BaseUserManager[User, int]):
    def parse_id(self, user_id: str) -> int:
        return int(user_id)

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")

# Authentication setup
cookie_transport = CookieTransport(cookie_name="salesstud_auth", cookie_max_age=3600)

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=settings.SECRET_KEY, lifetime_seconds=3600)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

def get_user_manager():
    return CustomUserManager(SQLAlchemyUserDatabase(next(get_db()), User))

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

# Google OAuth setup
google_oauth_client = GoogleOAuth2(
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
)

# JWT strategy for manual token creation
jwt_strategy = JWTStrategy(secret=settings.SECRET_KEY, lifetime_seconds=3600)

async def get_google_user_info(access_token: str):
    """Fetch user info from Google using access token"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        response.raise_for_status()
        return response.json()

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

# OAuth routes
@router.get("/google/authorize")
async def authorize_google():
    """Redirect to Google OAuth"""
    authorization_url = await google_oauth_client.get_authorization_url(
        redirect_uri="http://localhost:8000/auth/oauth/google/callback",
        state="random_state_string",  # In production, generate secure state
    )
    return {"authorization_url": authorization_url}

@router.get("/oauth/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code missing")

    # Exchange code for access token
    token = await google_oauth_client.get_access_token(code, "http://localhost:8000/auth/oauth/google/callback")

    # Get user info from Google
    user_info = await get_google_user_info(token["access_token"])

    email = user_info["email"]
    name = user_info.get("name", email.split("@")[0])

    # Check if user exists
    user = db.query(User).filter(User.email == email).first()

    if not user:
        # Create new user
        user = User(
            username=email.split("@")[0],
            full_name=name,
            email=email,
            hashed_password=None,  # OAuth users have no password
            role="SalesRep",
            is_active=True,
            auth_provider="google"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Create JWT token
    token_data = await jwt_strategy.write_token(user)

    # Set cookie and redirect
    response = RedirectResponse(url="http://localhost:3000", status_code=302)
    response.set_cookie(
        key="salesstud_auth",
        value=token_data,
        max_age=3600,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax"
    )
    return response

# Current user endpoint
@router.get("/me", response_model=UserRead)
async def get_current_user(user: User = Depends(fastapi_users.current_user())):
    return UserRead.from_orm(user)

# User preferences endpoints
class UserPreferencesUpdate(BaseModel):
    saved_tabs: list | None = None

@router.get("/preferences")
async def get_user_preferences(
    db: Session = Depends(get_db)
):
    """Get user preferences (demo: user_id=1)"""
    prefs = db.query(UserPreferences).filter(UserPreferences.user_id == 1).first()
    if not prefs:
        return {"saved_tabs": None}
    return {"saved_tabs": prefs.saved_tabs}

@router.post("/preferences")
async def save_user_preferences(
    prefs: UserPreferencesUpdate,
    db: Session = Depends(get_db)
):
    """Save user preferences (demo: user_id=1)"""
    existing_prefs = db.query(UserPreferences).filter(UserPreferences.user_id == 1).first()
    if existing_prefs:
        existing_prefs.saved_tabs = prefs.saved_tabs
        db.commit()
    else:
        new_prefs = UserPreferences(user_id=1, saved_tabs=prefs.saved_tabs)
        db.add(new_prefs)
        db.commit()
    return {"message": "Preferences saved successfully"}

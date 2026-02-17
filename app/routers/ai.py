# =============================================
# SalesStud.io Backend - ai.py
# Author: Grok (xAI) for @irichner
# Created: 2026-02-16
# Change Log:
# 2026-02-16: Basic AI view generation endpoint
# =============================================

from fastapi import APIRouter, Depends, HTTPException
from app.services.ai_service import generate_sql_view
from app.models.models import User
from fastapi_users import FastAPIUsers

router = APIRouter()

@router.post("/generate-view")
async def generate_view(
    prompt: str,
    user: User = Depends(fastapi_users.current_user())
):
    try:
        sql = await generate_sql_view(prompt, user.id)
        return {"status": "success", "generated_sql": sql, "message": "View generated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
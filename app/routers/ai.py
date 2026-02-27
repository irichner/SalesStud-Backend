# =============================================
# SalesStud.io Backend - ai.py
# Author: Grok (xAI) for @irichner
# Created: 2026-02-16
# Change Log:
# 2026-02-16: Basic AI view generation endpoint
# =============================================

from fastapi import APIRouter, Depends, HTTPException
from app.services.ai_service import generate_sql_view, generate_ai_response
from app.models.models import User, AIAgent, ChatMessage
from app.db.database import get_db
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.routers.auth import fastapi_users

# Pydantic models
class AIAgentCreate(BaseModel):
    name: str
    system_prompt: str
    user_prompt_template: Optional[str] = None
    tools: Optional[List[dict]] = None
    model: str
    provider_id: int

class ChatRequest(BaseModel):
    message: str
    agent_id: Optional[int] = None
    tab_id: str
    account_id: Optional[int] = None

class ChatMessageCreate(BaseModel):
    tab_id: str
    account_id: Optional[int] = None
    message_type: str
    content: str
    agent_id: Optional[int] = None

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

@router.post("/agents")
async def create_agent(
    agent_data: AIAgentCreate,
    user: User = Depends(fastapi_users.current_user()),
    db: Session = Depends(get_db)
):
    try:
        agent = AIAgent(
            name=agent_data.name,
            system_prompt=agent_data.system_prompt,
            user_prompt_template=agent_data.user_prompt_template,
            tools=agent_data.tools,
            model=agent_data.model,
            provider_id=agent_data.provider_id,
            created_by_user_id=user.id
        )
        db.add(agent)
        db.commit()
        db.refresh(agent)
        return {"status": "success", "agent": agent, "message": "Agent created successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents")
async def list_agents(
    user: User = Depends(fastapi_users.current_user()),
    db: Session = Depends(get_db)
):
    try:
        agents = db.query(AIAgent).filter(AIAgent.created_by_user_id == user.id).all()
        return {"status": "success", "agents": agents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def chat(
    request: ChatRequest,
    user: User = Depends(fastapi_users.current_user()),
    db: Session = Depends(get_db)
):
    try:
        # For now, use a default agent if none specified
        agent_id = request.agent_id or 1  # TODO: Make configurable

        # Get recent chat history for context
        recent_messages = db.query(ChatMessage).filter(
            ChatMessage.tab_id == request.tab_id,
            ChatMessage.user_id == user.id
        ).order_by(ChatMessage.timestamp.desc()).limit(10).all()
        recent_messages.reverse()  # Oldest first

        context = {
            "previous_messages": [
                {"role": "user" if msg.message_type == "user" else "assistant", "content": msg.content}
                for msg in recent_messages
            ]
        }

        # Generate response
        response = await generate_ai_response(agent_id, request.message, user.id, context)

        # Save user message
        user_msg = ChatMessage(
            tab_id=request.tab_id,
            account_id=request.account_id,
            user_id=user.id,
            message_type="user",
            content=request.message,
            agent_id=agent_id
        )
        db.add(user_msg)

        # Save AI response
        ai_msg = ChatMessage(
            tab_id=request.tab_id,
            account_id=request.account_id,
            user_id=user.id,
            message_type="ai",
            content=response,
            agent_id=agent_id
        )
        db.add(ai_msg)

        db.commit()

        return {"status": "success", "response": response}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/history/{tab_id}")
async def get_chat_history(
    tab_id: str,
    user: User = Depends(fastapi_users.current_user()),
    db: Session = Depends(get_db)
):
    try:
        messages = db.query(ChatMessage).filter(
            ChatMessage.tab_id == tab_id,
            ChatMessage.user_id == user.id
        ).order_by(ChatMessage.timestamp).all()
        return {"status": "success", "messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

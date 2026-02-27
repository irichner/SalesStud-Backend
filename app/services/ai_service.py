# =============================================
# SalesStud.io Backend - ai_service.py
# Author: Grok (xAI) for @irichner
# Created: 2026-02-16
# Change Log:
# 2026-02-16: Placeholder for LLM view/proc generation
# 2026-02-25: Multi-provider support and logging
# =============================================

import litellm
from app.core.config import settings
from app.db.database import get_db
from app.models.models import AIProvider, LLMSpendLog, AIAgent
from sqlalchemy.orm import Session
import asyncio

# Approximate pricing per 1K tokens (input/output combined for simplicity)
MODEL_PRICING = {
    "gpt-4o-mini": 0.00015,
    "gpt-4": 0.03,
    "gpt-4-turbo": 0.01,
    "gpt-3.5-turbo": 0.002,
    "grok-beta": 0.0001,  # Example for XAI
    # Add more as needed
}

async def get_active_provider(db: Session) -> AIProvider:
    """Get the first active provider (TODO: make configurable)"""
    provider = db.query(AIProvider).first()
    if not provider:
        raise ValueError("No AI provider configured")
    return provider

def calculate_cost(model: str, tokens: int) -> float:
    """Calculate approximate cost"""
    rate = MODEL_PRICING.get(model, 0.001)  # Default rate
    return (tokens / 1000) * rate

async def generate_sql_view(prompt: str, user_id: int) -> str:
    """Generate a safe SQL VIEW based on user prompt"""
    db = next(get_db())  # Get DB session
    try:
        provider = await get_active_provider(db)

        model = provider.default_model or "xai/grok-4-1-fast-reasoning"

        system_prompt = f"""You are an expert MSSQL developer for SalesStud.io.
        Only output valid CREATE VIEW or ALTER VIEW statements.
        Use existing tables: Users, Interactions, Opportunities, SalesTransactions, etc.
        Make it efficient and secure."""

        response = litellm.completion(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            api_key=provider.api_key,
            base_url=provider.base_url
        )

        sql = response.choices[0].message.content.strip()

        # Log usage
        tokens_used = response.usage.total_tokens if response.usage else 0
        cost = calculate_cost(model, tokens_used)

        log_entry = LLMSpendLog(
            user_id=user_id,
            provider=provider.provider_name,
            model=model,
            prompt=prompt,
            tokens=tokens_used,
            cost=cost
        )
        db.add(log_entry)
        db.commit()

        # TODO: Add SQL validation + execution later
        return sql
    finally:
        db.close()

async def generate_ai_response(agent_id: int, user_input: str, user_id: int, context: dict = None) -> str:
    """Generate AI response using an agent configuration"""
    db = next(get_db())  # Get DB session
    try:
        # Load agent
        agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
        if not agent:
            raise ValueError("Agent not found")

        # Get provider
        provider = agent.provider

        model = agent.model

        # Build messages
        messages = [
            {"role": "system", "content": agent.system_prompt}
        ]

        # Add context if provided (e.g., previous messages)
        if context and "previous_messages" in context:
            for msg in context["previous_messages"]:
                messages.append({"role": msg["role"], "content": msg["content"]})

        # Add user input
        if agent.user_prompt_template:
            user_content = agent.user_prompt_template.format(user_input=user_input)
        else:
            user_content = user_input
        messages.append({"role": "user", "content": user_content})

        # Make API call
        response = litellm.completion(
            model=model,
            messages=messages,
            temperature=0.7,  # Default, can be made configurable
            tools=agent.tools if agent.tools else None,
            api_key=provider.api_key,
            base_url=provider.base_url
        )

        ai_response = response.choices[0].message.content.strip()

        # Log usage
        tokens_used = response.usage.total_tokens if response.usage else 0
        cost = calculate_cost(model, tokens_used)

        log_entry = LLMSpendLog(
            user_id=user_id,
            provider=provider.provider_name,
            model=model,
            prompt=user_input,  # Log the user input
            tokens=tokens_used,
            cost=cost
        )
        db.add(log_entry)
        db.commit()

        return ai_response
    finally:
        db.close()

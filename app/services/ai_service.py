# =============================================
# SalesStud.io Backend - ai_service.py
# Author: Grok (xAI) for @irichner
# Created: 2026-02-16
# Change Log:
# 2026-02-16: Placeholder for LLM view/proc generation
# =============================================

from openai import OpenAI
from app.core.config import settings

client = OpenAI()

async def generate_sql_view(prompt: str, user_id: int) -> str:
    """Generate a safe SQL VIEW based on user prompt"""
    system_prompt = f"""You are an expert MSSQL developer for SalesStud.io.
    Only output valid CREATE VIEW or ALTER VIEW statements.
    Use existing tables: Users, Interactions, Opportunities, SalesTransactions, etc.
    Make it efficient and secure."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0
    )
    
    sql = response.choices[0].message.content.strip()
    # TODO: Add SQL validation + execution later
    return sql
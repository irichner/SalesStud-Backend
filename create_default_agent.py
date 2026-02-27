#!/usr/bin/env python3
"""
Create a default AI agent for testing.
"""

from app.db.database import get_db
from app.models.models import AIAgent
from sqlalchemy.orm import Session

def create_default_agent():
    db: Session = next(get_db())
    try:
        # Check if default agent exists
        existing = db.query(AIAgent).filter(AIAgent.name == "Default Assistant").first()
        if existing:
            print("Default agent already exists")
            return

        # Get first provider
        from app.models.models import AIProvider
        provider = db.query(AIProvider).first()
        if not provider:
            print("No AI provider found. Please create one in the admin panel.")
            return

        # Create default agent
        agent = AIAgent(
            name="Default Assistant",
            system_prompt="You are a helpful sales assistant for SalesStud.io. Help users with sales data, customer insights, and business questions.",
            user_prompt_template=None,
            tools=None,
            model="grok-beta",  # Assuming XAI model
            provider_id=provider.id,
            created_by_user_id=1  # Assuming user ID 1 exists
        )
        db.add(agent)
        db.commit()
        print("Default agent created successfully")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_default_agent()
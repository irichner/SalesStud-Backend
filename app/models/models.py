# =============================================
# SalesStud.io Backend - models.py
# Author: Grok (xAI) for @irichner
# Created: 2026-02-16
# Change Log:
# 2026-02-16: All core models + User for fastapi-users
# =============================================

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, DECIMAL, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
from fastapi_users.db import SQLAlchemyBaseUserTable

class User(Base, SQLAlchemyBaseUserTable[int]):
    __tablename__ = "Users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    role = Column(String(50), nullable=False)
    manager_id = Column(Integer, ForeignKey("Users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    auth_provider = Column(String(50), default="passkey")
    last_login = Column(DateTime(timezone=True), nullable=True)

    manager = relationship("User", remote_side=[id], backref="subordinates")

class Interaction(Base):
    __tablename__ = "Interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("Contacts.id"), nullable=True)
    opportunity_id = Column(Integer, ForeignKey("Opportunities.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("Users.id"), nullable=False)
    interaction_type = Column(String(50), nullable=False)
    channel = Column(String(50), nullable=False)
    interaction_date = Column(DateTime(timezone=True), nullable=False)
    subject = Column(String(500))
    body = Column(Text)
    summary = Column(Text)
    sentiment_score = Column(String(20))
    action_items_json = Column(JSON)
    recording_url = Column(String(500))
    meeting_platform = Column(String(50))

class CustomView(Base):
    __tablename__ = "CustomViews"
    
    id = Column(Integer, primary_key=True, index=True)
    view_name = Column(String(100), nullable=False)
    sql_code = Column(Text, nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("Users.id"))
    created_date = Column(DateTime(timezone=True), server_default=func.now())
# =============================================
# SalesStud.io Backend - models.py
# Author: Grok (xAI) for @irichner
# Created: 2026-02-16
# Change Log:
# 2026-02-16: All core models + User for fastapi-users
# =============================================

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, DECIMAL, JSON, Date
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
    company_name = Column(String(100), nullable=True)
    manager_id = Column(Integer, ForeignKey("Users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    auth_provider = Column(String(50), default="passkey")
    last_login = Column(DateTime(timezone=True), nullable=True)

    manager = relationship("User", remote_side=[id], backref="subordinates")

class Role(Base):
    __tablename__ = "Roles"

    id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))

class Permission(Base):
    __tablename__ = "Permissions"

    id = Column(Integer, primary_key=True, index=True)
    permission_name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255))

class UserRole(Base):
    __tablename__ = "UserRoles"

    user_id = Column(Integer, ForeignKey("Users.id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("Roles.id"), primary_key=True)

class RolePermission(Base):
    __tablename__ = "RolePermissions"

    role_id = Column(Integer, ForeignKey("Roles.id"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("Permissions.id"), primary_key=True)

class Account(Base):
    __tablename__ = "Accounts"

    id = Column("AccountID", Integer, primary_key=True, index=True)
    account_name = Column("AccountName", String(100), nullable=False)
    industry = Column("Industry", String(50))
    address = Column("Address", String(255))
    city = Column("City", String(50))
    state = Column("State", String(50))
    country = Column("Country", String(50))
    created_date = Column("CreatedDate", DateTime(timezone=True), server_default=func.now())
    updated_date = Column("UpdatedDate", DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Contact(Base):
    __tablename__ = "Contacts"

    id = Column("ContactID", Integer, primary_key=True, index=True)
    account_id = Column("AccountID", Integer, ForeignKey("Accounts.AccountID"), nullable=False)
    first_name = Column("FirstName", String(50), nullable=False)
    last_name = Column("LastName", String(50), nullable=False)
    email = Column("Email", String(100), unique=True)
    phone = Column("Phone", String(20))
    position = Column("Position", String(50))
    created_date = Column("CreatedDate", DateTime(timezone=True), server_default=func.now())
    updated_date = Column("UpdatedDate", DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    account = relationship("Account", backref="contacts")

class Opportunity(Base):
    __tablename__ = "Opportunities"

    id = Column("OpportunityID", Integer, primary_key=True, index=True)
    account_id = Column("AccountID", Integer, ForeignKey("Accounts.AccountID"), nullable=False)
    contact_id = Column("ContactID", Integer, ForeignKey("Contacts.ContactID"), nullable=True)
    opportunity_name = Column("OpportunityName", String(100), nullable=False)
    stage = Column("Stage", String(50), nullable=False)
    amount = Column("Amount", DECIMAL(18, 2), nullable=False)
    close_date = Column("CloseDate", Date)
    owner_id = Column("OwnerID", Integer, ForeignKey("Users.id"), nullable=False)
    created_date = Column("CreatedDate", DateTime(timezone=True), server_default=func.now())
    updated_date = Column("UpdatedDate", DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    account = relationship("Account", backref="opportunities")
    contact = relationship("Contact", backref="opportunities")
    owner = relationship("User", backref="opportunities")

class Product(Base):
    __tablename__ = "Products"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(100), nullable=False)
    description = Column(Text)
    price = Column(DECIMAL(18, 2), nullable=False)
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    updated_date = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class SalesTransaction(Base):
    __tablename__ = "SalesTransactions"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("Opportunities.OpportunityID"), nullable=True)
    product_id = Column(Integer, ForeignKey("Products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    amount = Column(DECIMAL(18, 2), nullable=False)
    transaction_date = Column(Date, nullable=False)
    sales_rep_id = Column(Integer, ForeignKey("Users.id"), nullable=False)
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    updated_date = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    opportunity = relationship("Opportunity", backref="transactions")
    product = relationship("Product", backref="transactions")
    sales_rep = relationship("User", backref="transactions")

class CommissionRule(Base):
    __tablename__ = "CommissionRules"

    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String(100), nullable=False)
    rule_type = Column(String(50), nullable=False)
    min_amount = Column(DECIMAL(18, 2))
    max_amount = Column(DECIMAL(18, 2))
    rate = Column(DECIMAL(5, 4), nullable=False)
    product_id = Column(Integer, ForeignKey("Products.id"), nullable=True)
    sales_rep_id = Column(Integer, ForeignKey("Users.id"), nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    updated_date = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    product = relationship("Product", backref="commission_rules")
    sales_rep = relationship("User", backref="commission_rules")

class Commission(Base):
    __tablename__ = "Commissions"

    id = Column(Integer, primary_key=True, index=True)
    sales_rep_id = Column(Integer, ForeignKey("Users.id"), nullable=False)
    transaction_id = Column(Integer, ForeignKey("SalesTransactions.id"), nullable=True)
    period = Column(String(50), nullable=False)
    calculated_amount = Column(DECIMAL(18, 2), nullable=False)
    rule_id = Column(Integer, ForeignKey("CommissionRules.id"), nullable=False)
    payout_date = Column(Date)
    status = Column(String(20), nullable=False)
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    updated_date = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    sales_rep = relationship("User", backref="commissions")
    transaction = relationship("SalesTransaction", backref="commissions")
    rule = relationship("CommissionRule", backref="commissions")

class Quota(Base):
    __tablename__ = "Quotas"

    id = Column(Integer, primary_key=True, index=True)
    sales_rep_id = Column(Integer, ForeignKey("Users.id"), nullable=False)
    period = Column(String(50), nullable=False)
    target_amount = Column(DECIMAL(18, 2), nullable=False)
    achieved_amount = Column(DECIMAL(18, 2), default=0)
    bonus_rate = Column(DECIMAL(5, 4))
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    updated_date = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    sales_rep = relationship("User", backref="quotas")

class Interaction(Base):
    __tablename__ = "Interactions"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("Contacts.ContactID"), nullable=True)
    opportunity_id = Column(Integer, ForeignKey("Opportunities.OpportunityID"), nullable=True)
    account_id = Column(Integer, ForeignKey("Accounts.AccountID"), nullable=True)
    user_id = Column(Integer, ForeignKey("Users.id"), nullable=False)
    interaction_type = Column(String(50), nullable=False)
    channel = Column(String(50), nullable=False)
    external_id = Column(String(255))
    direction = Column(String(20), nullable=False)
    interaction_date = Column(DateTime(timezone=True), nullable=False)
    subject = Column(String(500))
    body = Column(Text)
    raw_payload = Column(Text)
    summary = Column(Text)
    sentiment_score = Column(String(20))
    action_items_json = Column(JSON)
    recording_url = Column(String(500))
    meeting_platform = Column(String(50))
    participants_json = Column(JSON)
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    updated_date = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    contact = relationship("Contact", backref="interactions")
    opportunity = relationship("Opportunity", backref="interactions")
    account = relationship("Account", backref="interactions")
    user = relationship("User", backref="interactions")

class LLMSpendLog(Base):
    __tablename__ = "LLMSpendLogs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("Users.id"), nullable=False)
    prompt = Column(Text, nullable=False)
    tokens = Column(Integer, nullable=False)
    cost = Column(DECIMAL(10, 4), nullable=False)
    created_date = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="llm_spend_logs")

class CustomView(Base):
    __tablename__ = "CustomViews"

    id = Column(Integer, primary_key=True, index=True)
    view_name = Column(String(100), nullable=False)
    sql_code = Column(Text, nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("Users.id"))
    created_date = Column(DateTime(timezone=True), server_default=func.now())

    created_by = relationship("User", backref="custom_views")

class SPMProcHistory(Base):
    __tablename__ = "SPMProcHistory"

    id = Column(Integer, primary_key=True, index=True)
    proc_name = Column(String(100), nullable=False)
    sql_code = Column(Text, nullable=False)
    version = Column(Integer, nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("Users.id"))
    created_date = Column(DateTime(timezone=True), server_default=func.now())

    created_by = relationship("User", backref="spm_proc_history")

class UserPreferences(Base):
    __tablename__ = "UserPreferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("Users.id"), nullable=False)
    saved_tabs = Column(JSON, nullable=True)
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    updated_date = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", backref="preferences")

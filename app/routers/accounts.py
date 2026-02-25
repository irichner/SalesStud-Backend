# =============================================
# SalesStud.io Backend - accounts.py
# Author: Grok (xAI) for @irichner
# Created: 2026-02-23
# Change Log:
# 2026-02-23: CRUD operations for Accounts
# =============================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db.database import get_db
from app.models.models import Account, Contact, Opportunity
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

# Pydantic models
class AccountCreate(BaseModel):
    account_name: str
    industry: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

class AccountUpdate(BaseModel):
    account_name: Optional[str] = None
    industry: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

class AccountResponse(BaseModel):
    id: int
    account_name: str
    industry: Optional[str]
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    created_date: datetime
    updated_date: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[AccountResponse])
async def get_accounts(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all accounts with optional search"""
    query = db.query(Account)

    if search:
        query = query.filter(
            or_(
                Account.account_name.ilike(f"%{search}%"),
                Account.industry.ilike(f"%{search}%"),
                Account.city.ilike(f"%{search}%"),
                Account.state.ilike(f"%{search}%"),
                Account.country.ilike(f"%{search}%")
            )
        )

    accounts = query.order_by(Account.id).offset(skip).limit(limit).all()
    return accounts

@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(account_id: int, db: Session = Depends(get_db)):
    """Get a specific account by ID"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

@router.post("/", response_model=AccountResponse)
async def create_account(account: AccountCreate, db: Session = Depends(get_db)):
    """Create a new account"""
    db_account = Account(**account.dict())
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account

@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(account_id: int, account_update: AccountUpdate, db: Session = Depends(get_db)):
    """Update an account"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    update_data = account_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)

    db.commit()
    db.refresh(account)
    return account

@router.delete("/{account_id}")
async def delete_account(account_id: int, db: Session = Depends(get_db)):
    """Delete an account"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Check if account has related contacts or opportunities
    contacts_count = db.query(Contact).filter(Contact.account_id == account_id).count()
    opportunities_count = db.query(Opportunity).filter(Opportunity.account_id == account_id).count()

    if contacts_count > 0 or opportunities_count > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete account with existing contacts or opportunities"
        )

    db.delete(account)
    db.commit()
    return {"message": "Account deleted successfully"}

@router.get("/{account_id}/contacts")
async def get_account_contacts(account_id: int, db: Session = Depends(get_db)):
    """Get all contacts for an account"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    contacts = db.query(Contact).filter(Contact.account_id == account_id).all()
    return contacts

@router.get("/{account_id}/opportunities")
async def get_account_opportunities(account_id: int, db: Session = Depends(get_db)):
    """Get all opportunities for an account"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    opportunities = db.query(Opportunity).filter(Opportunity.account_id == account_id).all()
    return opportunities
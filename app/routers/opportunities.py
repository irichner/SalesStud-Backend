# =============================================
# SalesStud.io Backend - opportunities.py
# Author: Grok (xAI) for @irichner
# Created: 2026-02-23
# Change Log:
# 2026-02-23: CRUD operations for Opportunities
# =============================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.db.database import get_db
from app.models.models import Opportunity, Account, Contact, User, SalesTransaction
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date

router = APIRouter()

# Pydantic models
class OpportunityCreate(BaseModel):
    account_id: int
    contact_id: Optional[int] = None
    opportunity_name: str
    stage: str
    amount: float
    close_date: Optional[date] = None
    owner_id: int

class OpportunityUpdate(BaseModel):
    account_id: Optional[int] = None
    contact_id: Optional[int] = None
    opportunity_name: Optional[str] = None
    stage: Optional[str] = None
    amount: Optional[float] = None
    close_date: Optional[date] = None
    owner_id: Optional[int] = None

class OpportunityResponse(BaseModel):
    id: int
    account_id: int
    contact_id: Optional[int]
    opportunity_name: str
    stage: str
    amount: float
    close_date: Optional[date]
    owner_id: int
    created_date: datetime
    updated_date: datetime
    account_name: Optional[str] = None
    contact_name: Optional[str] = None
    owner_name: Optional[str] = None

    class Config:
        from_attributes = True

@router.get("/", response_model=List[OpportunityResponse])
async def get_opportunities(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    stage: Optional[str] = None,
    owner_id: Optional[int] = None,
    account_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all opportunities with optional filtering"""
    query = db.query(Opportunity).join(Account).join(User, Opportunity.owner_id == User.id).outerjoin(Contact)

    if search:
        query = query.filter(
            or_(
                Opportunity.opportunity_name.ilike(f"%{search}%"),
                Account.account_name.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%")
            )
        )

    if stage:
        query = query.filter(Opportunity.stage == stage)

    if owner_id:
        query = query.filter(Opportunity.owner_id == owner_id)

    if account_id:
        query = query.filter(Opportunity.account_id == account_id)

    opportunities = query.order_by(Opportunity.id).offset(skip).limit(limit).all()

    # Add related names
    result = []
    for opp in opportunities:
        opp_dict = OpportunityResponse.from_orm(opp).dict()
        opp_dict['account_name'] = opp.account.account_name
        opp_dict['owner_name'] = opp.owner.full_name
        if opp.contact:
            opp_dict['contact_name'] = f"{opp.contact.first_name} {opp.contact.last_name}"
        result.append(OpportunityResponse(**opp_dict))

    return result

@router.get("/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(opportunity_id: int, db: Session = Depends(get_db)):
    """Get a specific opportunity by ID"""
    opportunity = db.query(Opportunity).join(Account).join(User, Opportunity.owner_id == User.id).outerjoin(Contact).filter(Opportunity.id == opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    opp_dict = OpportunityResponse.from_orm(opportunity).dict()
    opp_dict['account_name'] = opportunity.account.account_name
    opp_dict['owner_name'] = opportunity.owner.full_name
    if opportunity.contact:
        opp_dict['contact_name'] = f"{opportunity.contact.first_name} {opportunity.contact.last_name}"
    return OpportunityResponse(**opp_dict)

@router.post("/", response_model=OpportunityResponse)
async def create_opportunity(opportunity: OpportunityCreate, db: Session = Depends(get_db)):
    """Create a new opportunity"""
    # Verify account exists
    account = db.query(Account).filter(Account.id == opportunity.account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Verify owner exists
    owner = db.query(User).filter(User.id == opportunity.owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")

    # Verify contact exists if provided
    if opportunity.contact_id:
        contact = db.query(Contact).filter(Contact.id == opportunity.contact_id).first()
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")

    # Validate stage
    valid_stages = ['Prospect', 'Qualification', 'Proposal', 'Negotiation', 'ClosedWon', 'ClosedLost']
    if opportunity.stage not in valid_stages:
        raise HTTPException(status_code=400, detail=f"Invalid stage. Must be one of: {', '.join(valid_stages)}")

    db_opportunity = Opportunity(**opportunity.dict())
    db.add(db_opportunity)
    db.commit()
    db.refresh(db_opportunity)

    opp_dict = OpportunityResponse.from_orm(db_opportunity).dict()
    opp_dict['account_name'] = account.account_name
    opp_dict['owner_name'] = owner.full_name
    if db_opportunity.contact:
        opp_dict['contact_name'] = f"{db_opportunity.contact.first_name} {db_opportunity.contact.last_name}"
    return OpportunityResponse(**opp_dict)

@router.put("/{opportunity_id}", response_model=OpportunityResponse)
async def update_opportunity(opportunity_id: int, opportunity_update: OpportunityUpdate, db: Session = Depends(get_db)):
    """Update an opportunity"""
    opportunity = db.query(Opportunity).join(Account).join(User, Opportunity.owner_id == User.id).outerjoin(Contact).filter(Opportunity.id == opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # Verify related entities if updating
    if opportunity_update.account_id:
        account = db.query(Account).filter(Account.id == opportunity_update.account_id).first()
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

    if opportunity_update.owner_id:
        owner = db.query(User).filter(User.id == opportunity_update.owner_id).first()
        if not owner:
            raise HTTPException(status_code=404, detail="Owner not found")

    if opportunity_update.contact_id:
        if opportunity_update.contact_id is not None:
            contact = db.query(Contact).filter(Contact.id == opportunity_update.contact_id).first()
            if not contact:
                raise HTTPException(status_code=404, detail="Contact not found")

    # Validate stage if updating
    if opportunity_update.stage:
        valid_stages = ['Prospect', 'Qualification', 'Proposal', 'Negotiation', 'ClosedWon', 'ClosedLost']
        if opportunity_update.stage not in valid_stages:
            raise HTTPException(status_code=400, detail=f"Invalid stage. Must be one of: {', '.join(valid_stages)}")

    update_data = opportunity_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(opportunity, field, value)

    db.commit()
    db.refresh(opportunity)

    opp_dict = OpportunityResponse.from_orm(opportunity).dict()
    opp_dict['account_name'] = opportunity.account.account_name
    opp_dict['owner_name'] = opportunity.owner.full_name
    if opportunity.contact:
        opp_dict['contact_name'] = f"{opportunity.contact.first_name} {opportunity.contact.last_name}"
    return OpportunityResponse(**opp_dict)

@router.delete("/{opportunity_id}")
async def delete_opportunity(opportunity_id: int, db: Session = Depends(get_db)):
    """Delete an opportunity"""
    opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # Check if opportunity has related transactions
    transactions_count = db.query(SalesTransaction).filter(SalesTransaction.opportunity_id == opportunity_id).count()

    if transactions_count > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete opportunity with existing transactions"
        )

    db.delete(opportunity)
    db.commit()
    return {"message": "Opportunity deleted successfully"}

@router.get("/{opportunity_id}/transactions")
async def get_opportunity_transactions(opportunity_id: int, db: Session = Depends(get_db)):
    """Get all transactions for an opportunity"""
    opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    transactions = db.query(SalesTransaction).filter(SalesTransaction.opportunity_id == opportunity_id).all()
    return transactions
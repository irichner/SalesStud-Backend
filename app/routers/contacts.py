# =============================================
# SalesStud.io Backend - contacts.py
# Author: Grok (xAI) for @irichner
# Created: 2026-02-23
# Change Log:
# 2026-02-23: CRUD operations for Contacts
# =============================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db.database import get_db
from app.models.models import Contact, Account, Opportunity
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

# Pydantic models
class ContactCreate(BaseModel):
    account_id: int
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None

class ContactUpdate(BaseModel):
    account_id: Optional[int] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None

class ContactResponse(BaseModel):
    id: int
    account_id: int
    first_name: str
    last_name: str
    email: Optional[str]
    phone: Optional[str]
    position: Optional[str]
    created_date: datetime
    updated_date: datetime
    account_name: Optional[str] = None

    class Config:
        from_attributes = True

@router.get("/", response_model=List[ContactResponse])
async def get_contacts(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    account_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all contacts with optional search and filtering"""
    query = db.query(Contact).join(Account)

    if search:
        query = query.filter(
            or_(
                Contact.first_name.ilike(f"%{search}%"),
                Contact.last_name.ilike(f"%{search}%"),
                Contact.email.ilike(f"%{search}%"),
                Contact.position.ilike(f"%{search}%"),
                Account.account_name.ilike(f"%{search}%")
            )
        )

    if account_id:
        query = query.filter(Contact.account_id == account_id)

    contacts = query.offset(skip).limit(limit).all()

    # Add account names
    result = []
    for contact in contacts:
        contact_dict = ContactResponse.from_orm(contact).dict()
        contact_dict['account_name'] = contact.account.account_name
        result.append(ContactResponse(**contact_dict))

    return result

@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(contact_id: int, db: Session = Depends(get_db)):
    """Get a specific contact by ID"""
    contact = db.query(Contact).join(Account).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    contact_dict = ContactResponse.from_orm(contact).dict()
    contact_dict['account_name'] = contact.account.account_name
    return ContactResponse(**contact_dict)

@router.post("/", response_model=ContactResponse)
async def create_contact(contact: ContactCreate, db: Session = Depends(get_db)):
    """Create a new contact"""
    # Verify account exists
    account = db.query(Account).filter(Account.id == contact.account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Check for duplicate email
    if contact.email:
        existing = db.query(Contact).filter(Contact.email == contact.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")

    db_contact = Contact(**contact.dict())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)

    contact_dict = ContactResponse.from_orm(db_contact).dict()
    contact_dict['account_name'] = account.account_name
    return ContactResponse(**contact_dict)

@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(contact_id: int, contact_update: ContactUpdate, db: Session = Depends(get_db)):
    """Update a contact"""
    contact = db.query(Contact).join(Account).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    # Verify account exists if updating account_id
    if contact_update.account_id:
        account = db.query(Account).filter(Account.id == contact_update.account_id).first()
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

    # Check for duplicate email
    if contact_update.email and contact_update.email != contact.email:
        existing = db.query(Contact).filter(Contact.email == contact_update.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")

    update_data = contact_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contact, field, value)

    db.commit()
    db.refresh(contact)

    contact_dict = ContactResponse.from_orm(contact).dict()
    contact_dict['account_name'] = contact.account.account_name
    return ContactResponse(**contact_dict)

@router.delete("/{contact_id}")
async def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    """Delete a contact"""
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    # Check if contact has related opportunities
    opportunities_count = db.query(Opportunity).filter(Opportunity.contact_id == contact_id).count()

    if opportunities_count > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete contact with existing opportunities"
        )

    db.delete(contact)
    db.commit()
    return {"message": "Contact deleted successfully"}

@router.get("/{contact_id}/opportunities")
async def get_contact_opportunities(contact_id: int, db: Session = Depends(get_db)):
    """Get all opportunities for a contact"""
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    opportunities = db.query(Opportunity).filter(Opportunity.contact_id == contact_id).all()
    return opportunities
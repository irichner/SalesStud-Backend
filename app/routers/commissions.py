# =============================================
# SalesStud.io Backend - commissions.py
# Author: Grok (xAI) for @irichner
# Created: 2026-02-23
# Change Log:
# 2026-02-23: CRUD operations for Commissions
# =============================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from app.db.database import get_db
from app.models.models import Commission, User, SalesTransaction, CommissionRule
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date

router = APIRouter()

# Pydantic models
class CommissionCreate(BaseModel):
    sales_rep_id: int
    transaction_id: Optional[int] = None
    period: str
    calculated_amount: float
    rule_id: int
    payout_date: Optional[date] = None
    status: str

class CommissionUpdate(BaseModel):
    sales_rep_id: Optional[int] = None
    transaction_id: Optional[int] = None
    period: Optional[str] = None
    calculated_amount: Optional[float] = None
    rule_id: Optional[int] = None
    payout_date: Optional[date] = None
    status: Optional[str] = None

class CommissionResponse(BaseModel):
    id: int
    sales_rep_id: int
    transaction_id: Optional[int]
    period: str
    calculated_amount: float
    rule_id: int
    payout_date: Optional[date]
    status: str
    created_date: datetime
    updated_date: datetime
    sales_rep_name: Optional[str] = None
    rule_name: Optional[str] = None

    class Config:
        from_attributes = True

@router.get("/", response_model=List[CommissionResponse])
async def get_commissions(
    skip: int = 0,
    limit: int = 100,
    sales_rep_id: Optional[int] = None,
    status: Optional[str] = None,
    period: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all commissions with optional filtering"""
    query = db.query(Commission).join(User, Commission.sales_rep_id == User.id).join(CommissionRule)

    if sales_rep_id:
        query = query.filter(Commission.sales_rep_id == sales_rep_id)

    if status:
        query = query.filter(Commission.status == status)

    if period:
        query = query.filter(Commission.period == period)

    commissions = query.order_by(Commission.id).offset(skip).limit(limit).all()

    # Add related names
    result = []
    for comm in commissions:
        comm_dict = CommissionResponse.from_orm(comm).dict()
        comm_dict['sales_rep_name'] = comm.sales_rep.full_name
        comm_dict['rule_name'] = comm.rule.rule_name
        result.append(CommissionResponse(**comm_dict))

    return result

@router.get("/{commission_id}", response_model=CommissionResponse)
async def get_commission(commission_id: int, db: Session = Depends(get_db)):
    """Get a specific commission by ID"""
    commission = db.query(Commission).join(User, Commission.sales_rep_id == User.id).join(CommissionRule).filter(Commission.id == commission_id).first()
    if not commission:
        raise HTTPException(status_code=404, detail="Commission not found")

    comm_dict = CommissionResponse.from_orm(commission).dict()
    comm_dict['sales_rep_name'] = commission.sales_rep.full_name
    comm_dict['rule_name'] = commission.rule.rule_name
    return CommissionResponse(**comm_dict)

@router.post("/", response_model=CommissionResponse)
async def create_commission(commission: CommissionCreate, db: Session = Depends(get_db)):
    """Create a new commission"""
    # Verify sales rep exists
    sales_rep = db.query(User).filter(User.id == commission.sales_rep_id).first()
    if not sales_rep:
        raise HTTPException(status_code=404, detail="Sales rep not found")

    # Verify rule exists
    rule = db.query(CommissionRule).filter(CommissionRule.id == commission.rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Commission rule not found")

    # Verify transaction exists if provided
    if commission.transaction_id:
        transaction = db.query(SalesTransaction).filter(SalesTransaction.id == commission.transaction_id).first()
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")

    # Validate status
    valid_statuses = ['Pending', 'Approved', 'Paid']
    if commission.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

    db_commission = Commission(**commission.dict())
    db.add(db_commission)
    db.commit()
    db.refresh(db_commission)

    comm_dict = CommissionResponse.from_orm(db_commission).dict()
    comm_dict['sales_rep_name'] = sales_rep.full_name
    comm_dict['rule_name'] = rule.rule_name
    return CommissionResponse(**comm_dict)

@router.put("/{commission_id}", response_model=CommissionResponse)
async def update_commission(commission_id: int, commission_update: CommissionUpdate, db: Session = Depends(get_db)):
    """Update a commission"""
    commission = db.query(Commission).join(User, Commission.sales_rep_id == User.id).join(CommissionRule).filter(Commission.id == commission_id).first()
    if not commission:
        raise HTTPException(status_code=404, detail="Commission not found")

    # Verify related entities if updating
    if commission_update.sales_rep_id:
        sales_rep = db.query(User).filter(User.id == commission_update.sales_rep_id).first()
        if not sales_rep:
            raise HTTPException(status_code=404, detail="Sales rep not found")

    if commission_update.rule_id:
        rule = db.query(CommissionRule).filter(CommissionRule.id == commission_update.rule_id).first()
        if not rule:
            raise HTTPException(status_code=404, detail="Commission rule not found")

    if commission_update.transaction_id:
        if commission_update.transaction_id is not None:
            transaction = db.query(SalesTransaction).filter(SalesTransaction.id == commission_update.transaction_id).first()
            if not transaction:
                raise HTTPException(status_code=404, detail="Transaction not found")

    # Validate status if updating
    if commission_update.status:
        valid_statuses = ['Pending', 'Approved', 'Paid']
        if commission_update.status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

    update_data = commission_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(commission, field, value)

    db.commit()
    db.refresh(commission)

    comm_dict = CommissionResponse.from_orm(commission).dict()
    comm_dict['sales_rep_name'] = commission.sales_rep.full_name
    comm_dict['rule_name'] = commission.rule.rule_name
    return CommissionResponse(**comm_dict)

@router.delete("/{commission_id}")
async def delete_commission(commission_id: int, db: Session = Depends(get_db)):
    """Delete a commission"""
    commission = db.query(Commission).filter(Commission.id == commission_id).first()
    if not commission:
        raise HTTPException(status_code=404, detail="Commission not found")

    db.delete(commission)
    db.commit()
    return {"message": "Commission deleted successfully"}

@router.get("/summary/{sales_rep_id}")
async def get_commission_summary(sales_rep_id: int, period: Optional[str] = None, db: Session = Depends(get_db)):
    """Get commission summary for a sales rep"""
    query = db.query(
        func.sum(Commission.calculated_amount).label('total_amount'),
        func.count(Commission.id).label('total_commissions'),
        Commission.status
    ).filter(Commission.sales_rep_id == sales_rep_id)

    if period:
        query = query.filter(Commission.period == period)

    query = query.group_by(Commission.status)

    results = query.all()

    summary = {
        'total_amount': 0,
        'total_commissions': 0,
        'by_status': {}
    }

    for row in results:
        summary['total_amount'] += float(row.total_amount or 0)
        summary['total_commissions'] += row.total_commissions
        summary['by_status'][row.status] = {
            'amount': float(row.total_amount or 0),
            'count': row.total_commissions
        }

    return summary
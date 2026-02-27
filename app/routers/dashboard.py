# =============================================
# SalesStud.io Backend - dashboard.py
# Author: Grok (xAI) for @irichner
# Created: 2026-02-23
# Change Log:
# 2026-02-23: Dashboard API endpoints for KPIs and charts
# =============================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case, extract, String, text
from app.db.database import get_db
from app.models.models import Opportunity, SalesTransaction, User
from fastapi_users import FastAPIUsers
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta

router = APIRouter()

# Pydantic models for responses
class KPICard(BaseModel):
    title: str
    value: str
    change: str
    icon: str
    positive: bool = True

class RevenueData(BaseModel):
    month: str
    revenue: float

class PipelineData(BaseModel):
    stage: str
    value: float

class OpportunityItem(BaseModel):
    id: int
    name: str
    account: str
    amount: float
    stage: str
    close_date: str | None
    owner: str

@router.get("/kpis", response_model=List[KPICard])
async def get_kpis(db: Session = Depends(get_db)):
    """Get dashboard KPI cards"""
    try:
        # Pipeline Value - sum of all opportunity amounts
        pipeline_result = db.query(func.sum(Opportunity.amount)).scalar()
        pipeline_value = pipeline_result or 0

        # Win Rate - percentage of closed won opportunities
        total_opps = db.query(func.count(Opportunity.id)).scalar()
        won_opps = db.query(func.count(Opportunity.id)).filter(Opportunity.stage == 'ClosedWon').scalar()
        win_rate = (won_opps / total_opps * 100) if total_opps > 0 else 0

        # Avg Deal Size - average amount of closed won opportunities
        avg_deal_result = db.query(func.avg(Opportunity.amount)).filter(Opportunity.stage == 'ClosedWon').scalar()
        avg_deal_size = avg_deal_result or 0

        # Deals Closed - count of closed won this month
        current_month = datetime.now().month
        current_year = datetime.now().year
        deals_closed = db.query(func.count(Opportunity.id)).filter(
            Opportunity.stage == 'ClosedWon',
            extract('month', Opportunity.updated_date) == current_month,
            extract('year', Opportunity.updated_date) == current_year
        ).scalar()

        kpis = [
            KPICard(
                title="Pipeline Value",
                value=f"${pipeline_value:,.0f}",
                change="+12.4%",  # TODO: Calculate actual change
                icon="target"
            ),
            KPICard(
                title="Win Rate",
                value=f"{win_rate:.1f}%",
                change="+3.2%",  # TODO: Calculate actual change
                icon="trend"
            ),
            KPICard(
                title="Avg Deal Size",
                value=f"${avg_deal_size:,.0f}",
                change="-2%",  # TODO: Calculate actual change
                icon="dollar",
                positive=False
            ),
            KPICard(
                title="Deals Closed",
                value=str(deals_closed),
                change="+7",  # TODO: Calculate actual change
                icon="users"
            )
        ]

        return kpis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/revenue-trend", response_model=List[RevenueData])
async def get_revenue_trend(db: Session = Depends(get_db)):
    """Get revenue trend data for the last 12 months"""
    try:
        # Check if there are any sales transactions
        transaction_count = db.query(func.count(SalesTransaction.id)).scalar()
        if transaction_count == 0:
            return []

        # Get revenue by month from sales transactions
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        # Fetch raw data and group in Python to avoid SQL dialect issues
        transactions = db.query(
            SalesTransaction.transaction_date,
            SalesTransaction.amount
        ).filter(
            SalesTransaction.transaction_date >= start_date.date(),
            SalesTransaction.transaction_date <= end_date.date()
        ).all()

        # Group by month in Python
        monthly_revenue = {}
        for transaction in transactions:
            # Create YYYY-MM key
            month_key = f"{transaction.transaction_date.year}-{transaction.transaction_date.month:02d}"
            if month_key not in monthly_revenue:
                monthly_revenue[month_key] = 0
            monthly_revenue[month_key] += float(transaction.amount)

        # Sort by month and format for response
        result = []
        for month_key in sorted(monthly_revenue.keys()):
            year, month = map(int, month_key.split('-'))
            month_date = datetime(year, month, 1)
            result.append(RevenueData(
                month=month_date.strftime('%b %Y'),
                revenue=monthly_revenue[month_key]
            ))

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pipeline-chart", response_model=List[PipelineData])
async def get_pipeline_chart(db: Session = Depends(get_db)):
    """Get pipeline data by stage"""
    try:
        pipeline_data = db.query(
            Opportunity.stage,
            func.sum(Opportunity.amount).label('value')
        ).group_by(Opportunity.stage).all()

        result = []
        for row in pipeline_data:
            result.append(PipelineData(
                stage=row.stage,
                value=float(row.value)
            ))

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recent-opportunities", response_model=List[OpportunityItem])
async def get_recent_opportunities(limit: int = 10, db: Session = Depends(get_db)):
    """Get recent opportunities"""
    try:
        # Check if there are any opportunities with non-null updated_date
        valid_opp_count = db.query(func.count(Opportunity.id)).filter(
            Opportunity.updated_date.isnot(None)
        ).scalar()
        if valid_opp_count == 0:
            return []

        opportunities = db.query(Opportunity).outerjoin(
            Opportunity.account
        ).outerjoin(
            Opportunity.owner
        ).filter(
            Opportunity.updated_date.isnot(None)
        ).order_by(
            Opportunity.updated_date.desc()
        ).limit(limit).all()

        result = []
        for opp in opportunities:
            result.append(OpportunityItem(
                id=opp.id,
                name=opp.opportunity_name,
                account=opp.account.account_name if opp.account else "Unknown Account",
                amount=float(opp.amount),
                stage=opp.stage,
                close_date=opp.close_date.isoformat() if opp.close_date else None,
                owner=opp.owner.full_name if opp.owner else "Unknown Owner"
            ))

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

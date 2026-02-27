# =============================================
# SalesStud.io Backend - admin.py
# Author: Grok (xAI) for @irichner
# Created: 2026-02-25
# Change Log:
# 2026-02-25: Admin endpoints for AI providers and metrics
# =============================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.db.database import get_db
from app.models.models import User, AIProvider, LLMSpendLog, SupportedAIProvider, SchemaProposal
from app.routers.auth import fastapi_users

router = APIRouter()

# Pydantic schemas
class AIProviderCreate(BaseModel):
    provider_name: str
    api_key: str
    base_url: Optional[str] = None
    models: Optional[List[str]] = None
    default_model: Optional[str] = None

class AIProviderRead(BaseModel):
    id: int
    provider_name: str
    api_key: str  # Note: In production, mask this
    base_url: Optional[str]
    models: Optional[List[str]]
    default_model: Optional[str]
    created_by_user_id: int
    created_date: datetime
    updated_date: datetime

    class Config:
        from_attributes = True

class AIProviderUpdate(BaseModel):
    provider_name: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    models: Optional[List[str]] = None
    default_model: Optional[str] = None

class MetricsResponse(BaseModel):
    provider: str
    model: str
    total_cost: float
    total_tokens: int
    usage_count: int

class SupportedProviderResponse(BaseModel):
    id: int
    provider_name: str
    base_url: str
    models: List[str]
    is_active: bool

    class Config:
        from_attributes = True

@router.get("/providers", response_model=List[AIProviderRead])
async def get_providers(
    db: Session = Depends(get_db),
    # user: User = Depends(fastapi_users.current_user())
):
    # if user.role != "Admin":
    #     raise HTTPException(status_code=403, detail="Admin access required")
    providers = db.query(AIProvider).all()
    return providers

@router.post("/providers", response_model=AIProviderRead)
async def create_provider(
    provider: AIProviderCreate,
    db: Session = Depends(get_db),
    # user: User = Depends(fastapi_users.current_user())
):
    # if user.role != "Admin":
    #     raise HTTPException(status_code=403, detail="Admin access required")
    new_provider = AIProvider(
        provider_name=provider.provider_name,
        api_key=provider.api_key,
        base_url=provider.base_url,
        models=provider.models,
        default_model=provider.default_model,
        created_by_user_id=1  # Hardcoded for testing
    )
    db.add(new_provider)
    db.commit()
    db.refresh(new_provider)
    return new_provider

@router.put("/providers/{provider_id}", response_model=AIProviderRead)
async def update_provider(
    provider_id: int,
    provider: AIProviderUpdate,
    db: Session = Depends(get_db),
    # user: User = Depends(fastapi_users.current_user())
):
    # if user.role != "Admin":
    #     raise HTTPException(status_code=403, detail="Admin access required")
    db_provider = db.query(AIProvider).filter(AIProvider.id == provider_id).first()
    if not db_provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    for key, value in provider.dict(exclude_unset=True).items():
        setattr(db_provider, key, value)
    db.commit()
    db.refresh(db_provider)
    return db_provider

@router.delete("/providers/{provider_id}")
async def delete_provider(
    provider_id: int,
    db: Session = Depends(get_db),
    # user: User = Depends(fastapi_users.current_user())
):
    # if user.role != "Admin":
    #     raise HTTPException(status_code=403, detail="Admin access required")
    db_provider = db.query(AIProvider).filter(AIProvider.id == provider_id).first()
    if not db_provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    db.delete(db_provider)
    db.commit()
    return {"message": "Provider deleted"}

@router.get("/metrics", response_model=List[MetricsResponse])
async def get_metrics(
    db: Session = Depends(get_db),
    # user: User = Depends(fastapi_users.current_user())
):
    # if user.role != "Admin":
    #     raise HTTPException(status_code=403, detail="Admin access required")
    # Aggregate metrics from LLMSpendLog
    results = db.query(
        LLMSpendLog.provider,
        LLMSpendLog.model,
        func.sum(LLMSpendLog.cost).label("total_cost"),
        func.sum(LLMSpendLog.tokens).label("total_tokens"),
        func.count(LLMSpendLog.id).label("usage_count")
    ).group_by(LLMSpendLog.provider, LLMSpendLog.model).all()

    return [
        MetricsResponse(
            provider=row.provider or "Unknown",
            model=row.model or "Unknown",
            total_cost=float(row.total_cost or 0),
            total_tokens=row.total_tokens or 0,
            usage_count=row.usage_count or 0
        ) for row in results if row.provider is not None and row.model is not None
    ]

@router.get("/supported-providers", response_model=List[SupportedProviderResponse])
async def get_supported_providers(
    db: Session = Depends(get_db),
    # user: User = Depends(fastapi_users.current_user())
):
    providers = db.query(SupportedAIProvider).filter(SupportedAIProvider.is_active == True).all()
    return providers

# Schema Evolution Schemas
class SchemaProposalCreate(BaseModel):
    reason: str
    desired_change: str

class SchemaProposalRead(BaseModel):
    id: int
    reason: str
    desired_change: str
    proposal_data: dict
    status: str
    risk_score: int
    created_by_user_id: int
    approved_by_user_id: Optional[int]
    created_date: datetime
    approved_date: Optional[datetime]

    class Config:
        from_attributes = True

class SchemaProposalApprove(BaseModel):
    approved: bool

# Schema Evolution Endpoints
@router.post("/schema-proposals", response_model=SchemaProposalRead)
async def create_schema_proposal(
    proposal: SchemaProposalCreate,
    db: Session = Depends(get_db),
    # user: User = Depends(fastapi_users.current_user())
):
    # if user.role != "Admin":
    #     raise HTTPException(status_code=403, detail="Admin access required")

    # Call the propose_schema_migration tool
    from app.services.schema_agent import propose_schema_migration
    proposal_data = propose_schema_migration.invoke({
        "reason": proposal.reason,
        "desired_change": proposal.desired_change
    })

    new_proposal = SchemaProposal(
        reason=proposal.reason,
        desired_change=proposal.desired_change,
        proposal_data=proposal_data,
        risk_score=proposal_data.get("risk_score", 5),
        created_by_user_id=1  # Hardcoded for testing
    )
    db.add(new_proposal)
    db.commit()
    db.refresh(new_proposal)
    return new_proposal

@router.get("/schema-proposals", response_model=List[SchemaProposalRead])
async def get_schema_proposals(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    # user: User = Depends(fastapi_users.current_user())
):
    # if user.role != "Admin":
    #     raise HTTPException(status_code=403, detail="Admin access required")
    query = db.query(SchemaProposal)
    if status:
        query = query.filter(SchemaProposal.status == status)
    proposals = query.all()
    return proposals

@router.put("/schema-proposals/{proposal_id}/approve")
async def approve_schema_proposal(
    proposal_id: int,
    approval: SchemaProposalApprove,
    db: Session = Depends(get_db),
    # user: User = Depends(fastapi_users.current_user())
):
    # if user.role != "Admin":
    #     raise HTTPException(status_code=403, detail="Admin access required")
    proposal = db.query(SchemaProposal).filter(SchemaProposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    if approval.approved:
        proposal.status = "approved"
        proposal.approved_by_user_id = 1  # Hardcoded
        proposal.approved_date = datetime.utcnow()

        # Apply the migration
        from app.services.schema_agent import apply_approved_migration
        result = apply_approved_migration.invoke({"proposal": proposal.proposal_data})
        proposal.status = "applied"
    else:
        proposal.status = "rejected"
        proposal.approved_by_user_id = 1  # Hardcoded
        proposal.approved_date = datetime.utcnow()

    db.commit()
    return {"message": f"Proposal {'approved and applied' if approval.approved else 'rejected'}"}

# =============================================
# SalesStud.io Backend - products.py
# Author: Grok (xAI) for @irichner
# Created: 2026-02-23
# Change Log:
# 2026-02-23: CRUD operations for Products
# =============================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db.database import get_db
from app.models.models import Product, SalesTransaction, CommissionRule
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

# Pydantic models
class ProductCreate(BaseModel):
    product_name: str
    description: Optional[str] = None
    price: float

class ProductUpdate(BaseModel):
    product_name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None

class ProductResponse(BaseModel):
    id: int
    product_name: str
    description: Optional[str]
    price: float
    created_date: datetime
    updated_date: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[ProductResponse])
async def get_products(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all products with optional search"""
    query = db.query(Product)

    if search:
        query = query.filter(
            or_(
                Product.product_name.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%")
            )
        )

    products = query.order_by(Product.id).offset(skip).limit(limit).all()
    return products

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a specific product by ID"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("/", response_model=ProductResponse)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product"""
    # Check for duplicate product name
    existing = db.query(Product).filter(Product.product_name == product.product_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Product name already exists")

    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(product_id: int, product_update: ProductUpdate, db: Session = Depends(get_db)):
    """Update a product"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check for duplicate product name
    if product_update.product_name and product_update.product_name != product.product_name:
        existing = db.query(Product).filter(Product.product_name == product_update.product_name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Product name already exists")

    update_data = product_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product

@router.delete("/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Delete a product"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check if product has related transactions or commission rules
    transactions_count = db.query(SalesTransaction).filter(SalesTransaction.product_id == product_id).count()
    commission_rules_count = db.query(CommissionRule).filter(CommissionRule.product_id == product_id).count()

    if transactions_count > 0 or commission_rules_count > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete product with existing transactions or commission rules"
        )

    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}

@router.get("/{product_id}/transactions")
async def get_product_transactions(product_id: int, db: Session = Depends(get_db)):
    """Get all transactions for a product"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    transactions = db.query(SalesTransaction).filter(SalesTransaction.product_id == product_id).all()
    return transactions

@router.get("/{product_id}/commission-rules")
async def get_product_commission_rules(product_id: int, db: Session = Depends(get_db)):
    """Get all commission rules for a product"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    commission_rules = db.query(CommissionRule).filter(CommissionRule.product_id == product_id).all()
    return commission_rules
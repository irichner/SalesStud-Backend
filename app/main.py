# =============================================
# SalesStud.io Backend - main.py
# Author: Grok (xAI) for @irichner
# Created: 2026-02-16
# Change Log:
# 2026-02-16: Added auth and ai routers
# =============================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.database import engine, Base
from app.routers import auth, dashboard, accounts, contacts, opportunities, products, commissions
# from app.routers import ai  # TODO: Add OpenAI API key

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="SalesStud.io API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
# app.include_router(ai.router, prefix="/ai", tags=["ai"])  # TODO: Add OpenAI API key
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
app.include_router(contacts.router, prefix="/contacts", tags=["contacts"])
app.include_router(opportunities.router, prefix="/opportunities", tags=["opportunities"])
app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(commissions.router, prefix="/commissions", tags=["commissions"])

@app.get("/")
async def root():
    return {"message": "✅ SalesStud.io Backend is running! (with auth + AI)"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
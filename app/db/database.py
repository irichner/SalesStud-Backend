# =============================================
# SalesStud.io Backend - database.py
# Author: Grok (xAI) for @irichner
# Created: 2026-02-16
# Change Log:
# 2026-02-16: SQLAlchemy engine + session
# =============================================

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# For SQL Server async, use mssql+aioodbc if available, else keep sync for now
# But to make it work, we'll use async with aiodriver if installed
try:
    engine = create_async_engine(
        settings.DATABASE_URL.replace("mssql+pyodbc", "mssql+aioodbc"),
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )
    is_async = True
except:
    # Fallback to sync
    from sqlalchemy import create_engine
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )
    is_async = False

if is_async:
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    Base = declarative_base()

    async def get_db():
        async with AsyncSessionLocal() as session:
            yield session
else:
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()

    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

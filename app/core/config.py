# =============================================
# SalesStud.io Backend - config.py
# Author: Grok (xAI) for @irichner
# Created: 2026-02-16
# Change Log:
# 2026-02-16: Initial Pydantic settings
# =============================================

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "mssql+pyodbc://sa:password@localhost/salesstud?driver=ODBC+Driver+17+for+SQL+Server"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
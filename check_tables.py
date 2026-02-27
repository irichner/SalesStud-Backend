from app.db.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")).fetchall()
    print([r[0] for r in result])
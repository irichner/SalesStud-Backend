from app.db.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text('DROP TABLE IF EXISTS [UserPreferences]'))
    conn.commit()
    print('Table dropped')
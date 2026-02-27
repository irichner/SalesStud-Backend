import app.models.models
from app.db.database import Base
print("Models in Base:")
for name, cls in Base.registry._class_registry.items():
    if hasattr(cls, '__tablename__'):
        print(f"  {cls.__tablename__}: {cls}")

from sqlalchemy import Column, String
from backend.app.db.base import Base

class Report(Base):
    __tablename__ = "reports"
    id = Column(String, primary_key=True)

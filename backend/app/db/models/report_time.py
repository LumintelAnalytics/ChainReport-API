from sqlalchemy import Column, String, DateTime, Float
from backend.app.db.base import Base

class ReportTime(Base):
    __tablename__ = "report_times"

    report_id = Column(String, primary_key=True, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)

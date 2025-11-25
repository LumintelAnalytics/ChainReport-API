from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.sql import func

from backend.app.db.database import Base


class ReportState(Base):
    __tablename__ = "report_states"

    report_id = Column(String, primary_key=True, index=True)
    status = Column(String, default="pending", index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    partial_agent_output = Column(JSON, nullable=True)  # Stores partial outputs from agents
    raw_data = Column(JSON, nullable=True)  # Stores raw data collected by agents
    final_report_json = Column(JSON, nullable=True)  # Stores the final generated report JSON

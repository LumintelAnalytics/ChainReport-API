from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.types import Enum as SQLEnum

from backend.app.db.database import Base

class ReportStatusEnum(PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    FAILED = "failed"
    COMPLETED = "completed"




class ReportState(Base):
    __tablename__ = "report_states"

    report_id = Column(String, ForeignKey("reports.id"), primary_key=True)
    status = Column(SQLEnum(ReportStatusEnum, values_callable=lambda x: [e.value for e in x]), default=ReportStatusEnum.PENDING, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    partial_agent_output = Column(JSON, nullable=True)  # Stores partial outputs from agents
    raw_data = Column(JSON, nullable=True)  # Stores raw data collected by agents
    final_report_json = Column(JSON, nullable=True)  # Stores the final generated report JSON

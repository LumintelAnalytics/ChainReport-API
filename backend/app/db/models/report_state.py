from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.types import Enum as SQLEnum

from backend.app.db.base import Base

class ReportStatusEnum(PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    FAILED = "failed"
    COMPLETED = "completed"
    RUNNING_AGENTS = "running_agents"
    AGENTS_COMPLETED = "agents_completed"
    AGENTS_FAILED = "agents_failed"
    AGENTS_PARTIAL_SUCCESS = "agents_partial_success"
    GENERATING_NLG = "generating_nlg"
    NLG_COMPLETED = "nlg_completed"
    GENERATING_SUMMARY = "generating_summary"
    SUMMARY_COMPLETED = "summary_completed"
    TIMED_OUT = "timed_out"




class ReportState(Base):
    __tablename__ = "report_states"

    report_id = Column(String, ForeignKey("reports.id"), primary_key=True)
    status = Column(SQLEnum(ReportStatusEnum, values_callable=lambda x: [e.value for e in x]), default=ReportStatusEnum.PENDING, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    partial_agent_output = Column(JSON, nullable=True)  # Stores partial outputs from agents
    raw_data = Column(JSON, nullable=True)  # Stores raw data collected by agents
    final_report_json = Column(JSON, nullable=True)  # Stores the final generated report JSON
    error_message = Column(String, nullable=True) # New column for error messages
    errors = Column(JSON, nullable=True) # Stores error flags for agents
    timing_alerts = Column(JSON, nullable=True) # Stores alerts related to processing times
    generation_time = Column(Float, nullable=True) # Stores the total time taken for report generation

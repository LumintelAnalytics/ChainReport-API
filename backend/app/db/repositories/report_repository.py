from typing import Callable, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from backend.app.db.models.report import Report
from backend.app.db.models.report_state import ReportState, ReportStatusEnum
class ReportRepository:
    def __init__(self, session_factory: Callable[..., AsyncSession]):
        self.session_factory = session_factory

    async def save_report_initial_state(self, report_id: str) -> ReportState:
        """
        Saves the initial state of a new report to the database.
        The report will be created with a PENDING status.
        """
        async with self.session_factory() as session:
            try:
                # Ensure a Report entry exists
                report = Report(id=report_id)
                session.add(report)
                
                # Create the initial ReportState
                report_state = ReportState(report_id=report_id, status=ReportStatusEnum.PENDING)
                session.add(report_state)
                
                await session.commit()
                await session.refresh(report_state)
                return report_state
            except IntegrityError:
                await session.rollback()
                # If a Report or ReportState with this ID already exists, fetch and return its state
                existing_state = await self.get_report_state(report_id)
                if existing_state:
                    return existing_state
                raise  # Re-raise if not found or other IntegrityError
            except Exception:
                await session.rollback()
                raise

    async def update_report_partial_results(self, report_id: str, partial_data: Dict[str, Any]) -> ReportState | None:
        """
        Updates the partial results of a report and sets its status to RUNNING if it's PENDING.
        """
        async with self.session_factory() as session:
            try:
                # Check current status
                current_state_result = await session.execute(select(ReportState.status).where(ReportState.report_id == report_id))
                current_status = current_state_result.scalar_one_or_none()

                if current_status in [ReportStatusEnum.COMPLETED, ReportStatusEnum.FAILED]:
                    # If the report is already in a final state, return its current state without modification
                    return await self.get_report_by_id(report_id)

                values_to_update = {
                    "partial_agent_output": partial_data,
                    "updated_at": datetime.now(timezone.utc)
                }

                if current_status == ReportStatusEnum.PENDING:
                    values_to_update["status"] = ReportStatusEnum.RUNNING
                
                stmt = update(ReportState).where(ReportState.report_id == report_id).values(**values_to_update).returning(ReportState)
                result = await session.execute(stmt)
                updated_report_state = result.scalar_one_or_none()
                await session.commit()
                return updated_report_state
            except Exception:
                await session.rollback()
                raise

    async def update_report_final_report(
        self, 
        report_id: str, 
        final_report_data: Optional[Dict[str, Any]], 
        status: ReportStatusEnum, 
        error_message: Optional[str] = None
    ) -> ReportState | None:
        """
        Updates the final report data, status, and optional error message.
        """
        async with self.session_factory() as session:
            try:
                values_to_update = {
                    "status": status,
                    "final_report_json": final_report_data,
                    "error_message": error_message,
                    "updated_at": datetime.now(timezone.utc)
                }
                stmt = update(ReportState).where(ReportState.report_id == report_id).values(**values_to_update).returning(ReportState)
                result = await session.execute(stmt)
                updated_report_state = result.scalar_one_or_none()
                await session.commit()
                return updated_report_state
            except Exception:
                await session.rollback()
                raise

    async def get_report_state(self, report_id: str) -> ReportState | None:
        """
        Retrieves the complete state of a report by its ID.
        """
        return await self.get_report_by_id(report_id)


    async def create_report_entry(self, report_id: str) -> Report:
        async with self.session_factory() as session:
            try:
                report = Report(id=report_id)
                session.add(report)
                report_state = ReportState(report_id=report_id, status=ReportStatusEnum.PENDING)
                session.add(report_state)
                await session.commit()
                await session.refresh(report)
                return report
            except IntegrityError:
                await session.rollback()
                # If a report with this ID already exists, fetch and return it
                existing_report = await session.execute(select(Report).where(Report.id == report_id))
                report = existing_report.scalar_one_or_none()
                if report:
                    return report
                else:
                    # This case should ideally not be reached if IntegrityError is due to report_id
                    raise
            except Exception:
                await session.rollback()
                raise

    async def update_report_status(self, report_id: str, status: ReportStatusEnum) -> ReportState | None:
        async with self.session_factory() as session:
            try:
                stmt = update(ReportState).where(ReportState.report_id == report_id).values(status=status).returning(ReportState)
                result = await session.execute(stmt)
                updated_report_state = result.scalar_one_or_none()
                await session.commit()
                return updated_report_state
            except Exception:
                await session.rollback()
                raise

    async def store_partial_report_results(self, report_id: str, partial_data: Dict[str, Any]) -> ReportState | None:
        async with self.session_factory() as session:
            try:
                stmt = update(ReportState).where(ReportState.report_id == report_id).values(partial_agent_output=partial_data).returning(ReportState)
                result = await session.execute(stmt)
                updated_report_state = result.scalar_one_or_none()
                await session.commit()
                return updated_report_state
            except Exception:
                await session.rollback()
                raise

    async def save_final_report(self, report_id: str, data: Dict[str, Any]) -> ReportState | None:
        async with self.session_factory() as session:
            try:
                stmt = update(ReportState).where(ReportState.report_id == report_id).values(final_report_json=data, status=ReportStatusEnum.COMPLETED).returning(ReportState)
                result = await session.execute(stmt)
                updated_report_state = result.scalar_one_or_none()
                await session.commit()
                return updated_report_state
            except Exception:
                await session.rollback()
                raise

    async def get_report_by_id(self, report_id: str) -> ReportState | None:
        async with self.session_factory() as session:
            stmt = select(ReportState).where(ReportState.report_id == report_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def update_timing_alerts(self, report_id: str, alerts: Dict[str, Any]) -> ReportState | None:
        async with self.session_factory() as session:
            try:
                stmt = update(ReportState).where(ReportState.report_id == report_id).values(timing_alerts=alerts).returning(ReportState)
                result = await session.execute(stmt)
                updated_report_state = result.scalar_one_or_none()
                await session.commit()
                return updated_report_state
            except Exception:
                await session.rollback()
                raise

    async def update_partial(self, report_id: str, data: Dict[str, Any]) -> ReportState | None:
        async with self.session_factory() as session:
            try:
                stmt = update(ReportState).where(ReportState.report_id == report_id).values(**data).returning(ReportState)
                result = await session.execute(stmt)
                updated_report_state = result.scalar_one_or_none()
                await session.commit()
                return updated_report_state
            except Exception:
                await session.rollback()
                raise

    async def recover_stalled_reports(self, timeout_minutes: int) -> int:
        async with self.session_factory() as session:
            try:
                stalled_threshold = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)
                
                running_states = [
                    ReportStatusEnum.RUNNING,
                    ReportStatusEnum.RUNNING_AGENTS,
                    ReportStatusEnum.GENERATING_NLG,
                    ReportStatusEnum.GENERATING_SUMMARY,
                ]

                stmt = update(ReportState).where(
                    ReportState.status.in_(running_states),
                    ReportState.updated_at < stalled_threshold
                ).values(
                    status=ReportStatusEnum.TIMED_OUT,
                    error_message="Report stalled in running state for too long."
                ).returning(ReportState.report_id)
                
                result = await session.execute(stmt)
                updated_report_ids = result.scalars().all()
                await session.commit()
                return len(updated_report_ids)
            except Exception:
                await session.rollback()
                raise


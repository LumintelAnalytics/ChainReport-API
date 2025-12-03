from typing import Callable, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from backend.app.db.models.report import Report
from backend.app.db.models.report_state import ReportState, ReportStatusEnum

class ReportRepository:
    def __init__(self, session_factory: Callable[..., AsyncSession]):
        self.session_factory = session_factory

    async def create_report_entry(self, report_id: str) -> Report:
        async with await self.session_factory() as session:
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
        async with await self.session_factory() as session:
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
        async with await self.session_factory() as session:
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
        async with await self.session_factory() as session:
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
        async with await self.session_factory() as session:
            stmt = select(ReportState).where(ReportState.report_id == report_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def update_timing_alerts(self, report_id: str, alerts: Dict[str, Any]) -> ReportState | None:
        async with await self.session_factory() as session:
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
        async with await self.session_factory() as session:
            try:
                stmt = update(ReportState).where(ReportState.report_id == report_id).values(**data).returning(ReportState)
                result = await session.execute(stmt)
                updated_report_state = result.scalar_one_or_none()
                await session.commit()
                return updated_report_state
            except Exception:
                await session.rollback()
                raise

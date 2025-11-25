from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from backend.app.db.models.report import Report
from backend.app.db.models.report_state import ReportState, ReportStatusEnum
from typing import Dict, Any

class ReportRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_report_entry(self, report_id: str) -> Report:
        report = Report(id=report_id)
        self.session.add(report)
        report_state = ReportState(report_id=report_id, status=ReportStatusEnum.PENDING)
        self.session.add(report_state)
        await self.session.commit()
        await self.session.refresh(report)
        await self.session.refresh(report_state)
        return report

    async def update_report_status(self, report_id: str, status: ReportStatusEnum) -> ReportState | None:
        stmt = update(ReportState).where(ReportState.report_id == report_id).values(status=status).returning(ReportState)
        result = await self.session.execute(stmt)
        updated_report_state = result.scalar_one_or_none()
        await self.session.commit()
        return updated_report_state

    async def store_partial_report_results(self, report_id: str, partial_data: Dict[str, Any]) -> ReportState | None:
        stmt = update(ReportState).where(ReportState.report_id == report_id).values(partial_agent_output=partial_data).returning(ReportState)
        result = await self.session.execute(stmt)
        updated_report_state = result.scalar_one_or_none()
        await self.session.commit()
        return updated_report_state

    async def save_final_report(self, report_id: str, data: Dict[str, Any]) -> ReportState | None:
        stmt = update(ReportState).where(ReportState.report_id == report_id).values(final_report_json=data, status=ReportStatusEnum.COMPLETED).returning(ReportState)
        result = await self.session.execute(stmt)
        updated_report_state = result.scalar_one_or_none()
        await self.session.commit()
        return updated_report_state

    async def get_report_state(self, report_id: str) -> ReportState | None:
        stmt = select(ReportState).where(ReportState.report_id == report_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from backend.app.db.models.report_time import ReportTime

class ReportTimeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_report_time(self, report_id: str, start_time: datetime) -> ReportTime:
        report_time = ReportTime(report_id=report_id, start_time=start_time)
        self.session.add(report_time)
        await self.session.commit()
        await self.session.refresh(report_time)
        return report_time

    async def get_report_time(self, report_id: str) -> ReportTime | None:
        result = await self.session.execute(select(ReportTime).filter(ReportTime.report_id == report_id))
        return result.scalars().first()

    async def update_report_time(self, report_id: str, end_time: datetime, duration: float) -> ReportTime | None:
        report_time = await self.get_report_time(report_id)
        if report_time:
            report_time.end_time = end_time
            report_time.duration = duration
            await self.session.commit()
            await self.session.refresh(report_time)
        return report_time

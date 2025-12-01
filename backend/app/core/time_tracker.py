from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.connection import get_db_session
from backend.app.db.repositories.report_time_repository import ReportTimeRepository

async def start_timer(report_id: str):
    """
    Records the start time for a given report_id.
    """
    async for session in get_db_session():
        repo = ReportTimeRepository(session)
        await repo.create_report_time(report_id, datetime.now())
        print(f"Timer started for report_id: {report_id} at {datetime.now()}")

async def finish_timer(report_id: str) -> Optional[float]:
    """
    Records the end time for a given report_id and computes the total duration.
    Returns the duration in seconds if successful, None otherwise.
    """
    async for session in get_db_session():
        repo = ReportTimeRepository(session)
        report_time_entry = await repo.get_report_time(report_id)
        if report_time_entry:
            end_time = datetime.now()
            duration = (end_time - report_time_entry.start_time).total_seconds()
            await repo.update_report_time(report_id, end_time, duration)
            print(f"Timer finished for report_id: {report_id} at {end_time}")
            print(f"Duration for report_id {report_id}: {duration:.2f} seconds")
            return duration
        print(f"Error: No start time found for report_id: {report_id}")
        return None

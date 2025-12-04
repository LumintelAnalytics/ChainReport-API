import pytest
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.app.db.base import Base
from backend.app.db.models.report import Report
from backend.app.db.models.report_state import ReportState, ReportStatusEnum
from backend.app.db.repositories.report_repository import ReportRepository

# Use a fixed timezone for consistency in tests
FIXED_TZ = timezone.utc

@pytest.fixture(name="async_session_factory")
async def async_session_factory_fixture():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    yield AsyncSessionLocal

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture(name="report_repository")
async def report_repository_fixture(async_session_factory):
    return ReportRepository(async_session_factory)

@pytest.mark.asyncio
async def test_recover_stalled_reports(report_repository, async_session_factory):
    async with async_session_factory() as session:
        # Create a report that is not stalled
        report_active = Report(id="report_active")
        report_state_active = ReportState(
            report_id="report_active",
            status=ReportStatusEnum.RUNNING,
            updated_at=datetime.now(FIXED_TZ) - timedelta(minutes=5)
        )
        session.add(report_active)
        session.add(report_state_active)

        # Create a report that is stalled
        report_stalled = Report(id="report_stalled")
        report_state_stalled = ReportState(
            report_id="report_stalled",
            status=ReportStatusEnum.RUNNING,
            updated_at=datetime.now(FIXED_TZ) - timedelta(minutes=65) # More than 60 minutes
        )
        session.add(report_stalled)
        session.add(report_state_stalled)

        # Create a report that is failed (should not be recovered)
        report_failed = Report(id="report_failed")
        report_state_failed = ReportState(
            report_id="report_failed",
            status=ReportStatusEnum.FAILED,
            updated_at=datetime.now(FIXED_TZ) - timedelta(minutes=70)
        )
        session.add(report_failed)
        session.add(report_state_failed)

        # Create a report that is completed (should not be recovered)
        report_completed = Report(id="report_completed")
        report_state_completed = ReportState(
            report_id="report_completed",
            status=ReportStatusEnum.COMPLETED,
            updated_at=datetime.now(FIXED_TZ) - timedelta(minutes=70)
        )
        session.add(report_completed)
        session.add(report_state_completed)

        await session.commit()

    # Recover stalled reports with a timeout of 60 minutes
    recovered_count = await report_repository.recover_stalled_reports(timeout_minutes=60)
    assert recovered_count == 1

    async with async_session_factory() as session:
        # Verify status of active report
        active_report_state = await session.execute(
            select(ReportState).where(ReportState.report_id == "report_active")
        )
        assert active_report_state.scalar_one().status == ReportStatusEnum.RUNNING

        # Verify status of stalled report
        stalled_report_state = await session.execute(
            select(ReportState).where(ReportState.report_id == "report_stalled")
        )
        recovered_stalled = stalled_report_state.scalar_one()
        assert recovered_stalled.status == ReportStatusEnum.TIMED_OUT
        assert recovered_stalled.error_message == "Report stalled in running state for too long."

        # Verify status of failed report
        failed_report_state = await session.execute(
            select(ReportState).where(ReportState.report_id == "report_failed")
        )
        assert failed_report_state.scalar_one().status == ReportStatusEnum.FAILED

        # Verify status of completed report
        completed_report_state = await session.execute(
            select(ReportState).where(ReportState.report_id == "report_completed")
        )
        assert completed_report_state.scalar_one().status == ReportStatusEnum.COMPLETED

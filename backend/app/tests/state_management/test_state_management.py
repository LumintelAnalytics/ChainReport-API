import pytest
from sqlalchemy import select
from datetime import datetime, timezone, timedelta
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
async def test_save_new_report_state(report_repository, async_session_factory):
    report_id = "test_report_1"
    
    # Test saving a new report
    initial_state = await report_repository.save_report_initial_state(report_id)
    assert initial_state.report_id == report_id
    assert initial_state.status == ReportStatusEnum.PENDING
    assert initial_state.partial_agent_output is None
    assert initial_state.final_report_json is None
    assert initial_state.error_message is None

    async with async_session_factory() as session:
        # Verify it's in the database
        db_state = await session.execute(
            select(ReportState).where(ReportState.report_id == report_id)
        )
        assert db_state.scalar_one().status == ReportStatusEnum.PENDING

@pytest.mark.asyncio
async def test_update_report_partial_results(report_repository, async_session_factory):
    report_id = "test_report_2"
    await report_repository.save_report_initial_state(report_id)

    partial_result_1 = {"step": 1, "data": "processing"}
    updated_state = await report_repository.update_report_partial_results(report_id, partial_result_1)

    assert updated_state.report_id == report_id
    assert updated_state.status == ReportStatusEnum.RUNNING
    assert updated_state.partial_agent_output == partial_result_1
    assert updated_state.final_report_json is None
    assert updated_state.error_message is None

    async with async_session_factory() as session:
        db_state = await session.execute(
            select(ReportState).where(ReportState.report_id == report_id)
        )
        db_state_obj = db_state.scalar_one()
        assert db_state_obj.status == ReportStatusEnum.RUNNING
        assert db_state_obj.partial_agent_output == partial_result_1
    
    # Update with more partial results
    partial_result_2 = {"step": 2, "data": "more processing"}
    updated_state_2 = await report_repository.update_report_partial_results(report_id, partial_result_2)
    assert updated_state_2.partial_agent_output == partial_result_2

@pytest.mark.asyncio
async def test_update_report_final_report_success(report_repository, async_session_factory):
    report_id = "test_report_3"
    await report_repository.save_report_initial_state(report_id)
    await report_repository.update_report_partial_results(report_id, {"step": 1})

    final_report_data = {"summary": "Final report data", "score": 95}
    final_state = await report_repository.update_report_final_report(
        report_id,
        final_report_data,
        ReportStatusEnum.COMPLETED
    )

    assert final_state.report_id == report_id
    assert final_state.status == ReportStatusEnum.COMPLETED
    assert final_state.final_report_json == final_report_data
    assert final_state.error_message is None

    async with async_session_factory() as session:
        db_state = await session.execute(
            select(ReportState).where(ReportState.report_id == report_id)
        )
        db_state_obj = db_state.scalar_one()
        assert db_state_obj.status == ReportStatusEnum.COMPLETED
        assert db_state_obj.final_report_json == final_report_data
@pytest.mark.asyncio
async def test_update_report_final_report_failure(report_repository, async_session_factory):
    report_id = "test_report_4"
    await report_repository.save_report_initial_state(report_id)

    error_message = "An error occurred during report generation."
    final_state = await report_repository.update_report_final_report(
        report_id,
        None,
        ReportStatusEnum.FAILED,
        error_message=error_message
    )

    assert final_state.report_id == report_id
    assert final_state.status == ReportStatusEnum.FAILED
    assert final_state.final_report_json is None
    assert final_state.error_message == error_message

    async with async_session_factory() as session:
        db_state = await session.execute(
            select(ReportState).where(ReportState.report_id == report_id)
        )
        db_state_obj = db_state.scalar_one()
        assert db_state_obj.status == ReportStatusEnum.FAILED
        assert db_state_obj.error_message == error_message

@pytest.mark.asyncio
async def test_get_report_state(report_repository, async_session_factory):
    report_id = "test_report_5"
    await report_repository.save_report_initial_state(report_id)

    # Get initial state
    state = await report_repository.get_report_state(report_id)
    assert state.report_id == report_id
    assert state.status == ReportStatusEnum.PENDING

    # Update to running
    await report_repository.update_report_partial_results(report_id, {"data": "step 1"})
    state = await report_repository.get_report_state(report_id)
    assert state.status == ReportStatusEnum.RUNNING
    assert state.partial_agent_output == {"data": "step 1"}

    # Update to completed
    final_data = {"final": "report"}
    await report_repository.update_report_final_report(report_id, final_data, ReportStatusEnum.COMPLETED)
    state = await report_repository.get_report_state(report_id)
    assert state.status == ReportStatusEnum.COMPLETED
    assert state.final_report_json == final_data

@pytest.mark.asyncio
async def test_report_state_transitions(report_repository, async_session_factory):
    report_id = "test_report_6"

    # 1. Initial state: PENDING
    state_pending = await report_repository.save_report_initial_state(report_id)
    assert state_pending.status == ReportStatusEnum.PENDING

    # 2. Transition to RUNNING with partial results
    partial_data = {"progress": 50}
    state_running = await report_repository.update_report_partial_results(report_id, partial_data)
    assert state_running.partial_agent_output == partial_data

    # 3. Transition to COMPLETED with final report
    final_data = {"result": "success"}
    state_completed = await report_repository.update_report_final_report(report_id, final_data, ReportStatusEnum.COMPLETED)
    assert state_completed.status == ReportStatusEnum.COMPLETED
    assert state_completed.final_report_json == final_data
    assert state_completed.error_message is None
    
    # Verify that updated_at changes
    assert state_completed.updated_at > state_running.updated_at

    # Try to update a completed report (should not change status/final report)
    # The repository methods should ideally prevent or handle invalid state transitions.
    # For now, we'll check that the report remains completed and no new error is added.
    original_updated_at = state_completed.updated_at
    unchanged_state = await report_repository.update_report_partial_results(report_id, {"progress": 100})
    assert unchanged_state.status == ReportStatusEnum.COMPLETED
    assert unchanged_state.final_report_json == final_data
    assert unchanged_state.updated_at > original_updated_at # updated_at still updates

@pytest.mark.asyncio
async def test_report_state_transitions_to_failed(report_repository, async_session_factory):
    report_id = "test_report_7"

    # 1. Initial state: PENDING
    state_pending = await report_repository.save_report_initial_state(report_id)
    assert state_pending.status == ReportStatusEnum.PENDING

    # 2. Transition to RUNNING with partial results
    partial_data = {"progress": 25}
    state_running = await report_repository.update_report_partial_results(report_id, partial_data)
    assert state_running.status == ReportStatusEnum.RUNNING
    assert state_running.partial_agent_output == partial_data

    # 3. Transition to FAILED with error message
    error_msg = "Critical error during processing."
    state_failed = await report_repository.update_report_final_report(report_id, None, ReportStatusEnum.FAILED, error_message=error_msg)
    assert state_failed.status == ReportStatusEnum.FAILED
    assert state_failed.final_report_json is None
    assert state_failed.error_message == error_msg
    
    # Verify that updated_at changes
    assert state_failed.updated_at > state_running.updated_at

    # Try to update a failed report (should not change status/final report)
    original_updated_at = state_failed.updated_at
    unchanged_state = await report_repository.update_report_partial_results(report_id, {"progress": 75})
    assert unchanged_state.status == ReportStatusEnum.FAILED
    assert unchanged_state.error_message == error_msg
    assert unchanged_state.updated_at > original_updated_at # updated_at still updates

@pytest.mark.asyncio
async def test_report_not_found(report_repository):
    report_id = "non_existent_report"
    state = await report_repository.get_report_state(report_id)
    assert state is None

    # Test updating a non-existent report
    updated_state = await report_repository.update_report_partial_results(report_id, {"data": "test"})
    assert updated_state is None

    final_state = await report_repository.update_report_final_report(report_id, {"data": "final"}, ReportStatusEnum.COMPLETED)
    assert final_state is None

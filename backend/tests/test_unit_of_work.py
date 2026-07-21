import pytest_asyncio
from datetime import datetime

from src.domain.entities.file import File
from src.domain.entities.processing_task import ProcessingTask
from src.domain.entities.task_execution import TaskExecution
from src.domain.enums import (
    FileStatus,
    PipelineType,
    ProcessingTaskStatus,
    ProcessorType,
    TaskExecutionStatus,
)
from src.infrastructure.database import DatabaseSessionManager
from src.infrastructure.database.unit_of_work import SQLUnitOfWork


@pytest_asyncio.fixture
async def test_db_manager(test_engine):
    """Create a test DatabaseSessionManager using the test engine."""
    manager = DatabaseSessionManager("sqlite+aiosqlite://")
    manager._engine = test_engine
    from sqlalchemy.ext.asyncio import async_sessionmaker

    manager._session_maker = async_sessionmaker(test_engine, expire_on_commit=False)
    return manager


async def test_uow_commit_persists_data(test_db_manager, db_session):
    """Test that commit persists data to database."""
    async with SQLUnitOfWork(test_db_manager) as uow:
        file = File(
            id="test-file-1",
            title="Test File",
            original_name="test.txt",
            stored_name="test-file-1.txt",
            mime_type="text/plain",
            size=100,
            status=FileStatus.NEW,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        saved = await uow.file_repo.save(file)
        assert saved.id == "test-file-1"
        await uow.commit()

    # Should be visible in new UoW
    async with SQLUnitOfWork(test_db_manager) as uow2:
        found = await uow2.file_repo.get_by_id("test-file-1")
        assert found is not None
        assert found.title == "Test File"


async def test_uow_rollback_discards_changes(test_db_manager, db_session):
    """Test that rollback discards uncommitted changes."""
    async with SQLUnitOfWork(test_db_manager) as uow:
        file = File(
            id="test-file-2",
            title="Test File 2",
            original_name="test2.txt",
            stored_name="test-file-2.txt",
            mime_type="text/plain",
            size=200,
            status=FileStatus.NEW,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        await uow.file_repo.save(file)
        await uow.rollback()

    # Should NOT be visible in new UoW
    async with SQLUnitOfWork(test_db_manager) as uow2:
        found = await uow2.file_repo.get_by_id("test-file-2")
        assert found is None


async def test_uow_without_commit_not_visible_in_new_uow(test_db_manager, db_session):
    """Test that changes without commit are not visible in new UoW."""
    async with SQLUnitOfWork(test_db_manager) as uow:
        file = File(
            id="test-file-3",
            title="Test File 3",
            original_name="test3.txt",
            stored_name="test-file-3.txt",
            mime_type="text/plain",
            size=300,
            status=FileStatus.NEW,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        saved = await uow.file_repo.save(file)
        assert saved.id == "test-file-3"
        await uow.flush()  # Flush but don't commit

    # Should NOT be visible in new UoW (no commit)
    async with SQLUnitOfWork(test_db_manager) as uow2:
        found = await uow2.file_repo.get_by_id("test-file-3")
        assert found is None


async def test_uow_repositories_share_session(test_db_manager, db_session):
    """Test that all repositories in UoW share the same session."""
    async with SQLUnitOfWork(test_db_manager) as uow:
        # Create file
        file = File(
            id="test-file-4",
            title="Test File 4",
            original_name="test4.txt",
            stored_name="test-file-4.txt",
            mime_type="text/plain",
            size=400,
            status=FileStatus.NEW,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        await uow.file_repo.save(file)

        # Create processing task for same file
        task = ProcessingTask(
            file_id="test-file-4",
            pipeline_type=PipelineType.DEFAULT_FILE_PROCESSING,
            status=ProcessingTaskStatus.PENDING,
        )
        await uow.processing_task_repo.save(task)

        # Create task execution for same task
        execution = TaskExecution(
            processing_task_id=1,  # Will be set after task is saved
            processor=ProcessorType.METADATA_EXTRACTOR,
            status=TaskExecutionStatus.PENDING,
        )
        await uow.task_execution_repo.save(execution)

        await uow.commit()

    # All should be visible in new UoW
    async with SQLUnitOfWork(test_db_manager) as uow2:
        found_file = await uow2.file_repo.get_by_id("test-file-4")
        assert found_file is not None

        tasks = await uow2.processing_task_repo.list_for_file("test-file-4")
        assert len(tasks) == 1

        executions = await uow2.task_execution_repo.list_for_processing_task(
            tasks[0].id
        )
        assert len(executions) == 1


async def test_uow_can_update_entities(test_db_manager, db_session):
    """Test that UoW can update existing entities."""
    # Create initial file
    async with SQLUnitOfWork(test_db_manager) as uow:
        file = File(
            id="test-file-5",
            title="Original Title",
            original_name="test5.txt",
            stored_name="test-file-5.txt",
            mime_type="text/plain",
            size=500,
            status=FileStatus.NEW,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        await uow.file_repo.save(file)
        await uow.commit()

    # Update in new UoW
    async with SQLUnitOfWork(test_db_manager) as uow:
        file = await uow.file_repo.get_by_id("test-file-5")
        assert file is not None
        file.title = "Updated Title"
        file.status = FileStatus.OK
        await uow.file_repo.save(file)
        await uow.commit()

    # Verify update
    async with SQLUnitOfWork(test_db_manager) as uow:
        file = await uow.file_repo.get_by_id("test-file-5")
        assert file.title == "Updated Title"
        assert file.status == FileStatus.OK


async def test_uow_delete(test_db_manager, db_session):
    """Test that UoW can delete entities."""
    # Create file
    async with SQLUnitOfWork(test_db_manager) as uow:
        file = File(
            id="test-file-6",
            title="Test File 6",
            original_name="test6.txt",
            stored_name="test-file-6.txt",
            mime_type="text/plain",
            size=600,
            status=FileStatus.NEW,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        await uow.file_repo.save(file)
        await uow.commit()

    # Delete in new UoW
    async with SQLUnitOfWork(test_db_manager) as uow:
        file = await uow.file_repo.get_by_id("test-file-6")
        await uow.file_repo.delete(file)
        await uow.commit()

    # Verify deletion
    async with SQLUnitOfWork(test_db_manager) as uow:
        found = await uow.file_repo.get_by_id("test-file-6")
        assert found is None

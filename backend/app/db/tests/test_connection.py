import pytest
import os
from dotenv import load_dotenv
from backend.app.db.connection import DatabaseConnection, initialize_db_connection, close_db_connection

# Load environment variables from .env file for testing
load_dotenv()

@pytest.fixture(scope="module", autouse=True)
async def setup_and_teardown_db():
    # Ensure environment variables are set for testing
    os.environ["DB_USER"] = os.getenv("TEST_DB_USER", "postgres")
    os.environ["DB_PASSWORD"] = os.getenv("TEST_DB_PASSWORD", "postgres")
    os.environ["DB_HOST"] = os.getenv("TEST_DB_HOST", "localhost")
    os.environ["DB_PORT"] = os.getenv("TEST_DB_PORT", "5432")
    os.environ["DB_NAME"] = os.getenv("TEST_DB_NAME", "test_db")

    await initialize_db_connection()
    yield
    await close_db_connection()

@pytest.mark.asyncio
async def test_database_connection_pool():
    pool = await DatabaseConnection.connect()
    assert pool is not None
    assert pool.get_size() >= 1

    conn = await DatabaseConnection.get_connection()
    assert conn is not None
    await DatabaseConnection.release_connection(conn)

@pytest.mark.asyncio
async def test_get_and_release_connection():
    conn = await DatabaseConnection.get_connection()
    assert conn is not None
    # You can execute a simple query to verify the connection
    result = await conn.fetchval("SELECT 1")
    assert result == 1
    await DatabaseConnection.release_connection(conn)

@pytest.mark.asyncio
async def test_disconnect():
    await DatabaseConnection.disconnect()
    assert DatabaseConnection._pool is None
    # Reconnect for subsequent tests in the same module
    await DatabaseConnection.connect()

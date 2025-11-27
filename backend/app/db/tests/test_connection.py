import pytest
import os
from dotenv import load_dotenv
from backend.app.db.connection import DatabaseConnection, initialize_db_connection, close_db_connection
import unittest.mock

# Load environment variables from .env file for testing
load_dotenv()

@pytest.fixture(scope="module", autouse=True)
async def setup_and_teardown_db():
    # Mock asyncpg.create_pool and related methods
    with unittest.mock.patch('asyncpg.create_pool', new_callable=unittest.mock.AsyncMock) as mock_create_pool:
        mock_pool_instance = unittest.mock.AsyncMock()
        mock_conn_instance = unittest.mock.AsyncMock()
        mock_conn_instance.fetchval.return_value = 1
        mock_pool_instance.acquire.return_value = mock_conn_instance
        mock_pool_instance.get_size = unittest.mock.MagicMock(return_value=5)  # Mock the return value for get_size
        mock_create_pool.return_value = mock_pool_instance

        # Use mock environment variables for testing database connection
        with unittest.mock.patch.dict(os.environ, {
            "DB_USER": "test_user",
            "DB_PASSWORD": "test_password",
            "DB_HOST": "mock_host",
            "DB_PORT": "5432",
            "DB_NAME": "mock_db",
        }):
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


import os
import asyncpg
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class DatabaseConnection:
    _pool = None
    _pool_lock = asyncio.Lock()

    @classmethod
    async def connect(cls):
        if cls._pool is None:
            async with cls._pool_lock:
                if cls._pool is None:
                    try:
                        db_user = os.getenv("DB_USER")
                        db_password = os.getenv("DB_PASSWORD")
                        db_host = os.getenv("DB_HOST")
                        db_port_str = os.getenv("DB_PORT")
                        db_name = os.getenv("DB_NAME")

                        missing_vars = [
                            name for name, value in {
                                "DB_USER": db_user,
                                "DB_PASSWORD": db_password,
                                "DB_HOST": db_host,
                                "DB_PORT": db_port_str,
                                "DB_NAME": db_name,
                            }.items() if not value
                        ]

                        if missing_vars:
                            raise ValueError(
                                f"Missing or empty database environment variables: {', '.join(missing_vars)}"
                            )

                        try:
                            db_port = int(db_port_str)
                        except (TypeError, ValueError) as e:
                            raise ValueError(f"DB_PORT must be an integer: {e}") from e

                        cls._pool = await asyncpg.create_pool(
                            user=db_user,
                            password=db_password,
                            host=db_host,
                            port=db_port,
                            database=db_name,
                            min_size=1,
                            max_size=10,
                        )
                        logger.info("Database connection pool created successfully.")
                    except Exception:
                        logger.error("Error connecting to the database.", exc_info=True)
                        raise
        return cls._pool

    @classmethod
    async def disconnect(cls):
        if cls._pool:
            logger.info("Closing database connection pool.")
            await cls._pool.close()
            cls._pool = None
            logger.info("Database connection pool closed.")

    @classmethod
    async def get_connection(cls):
        if cls._pool is None:
            await cls.connect()
        return await cls._pool.acquire(timeout=30)

    @classmethod
    async def release_connection(cls, conn):
        if cls._pool and conn:
            await cls._pool.release(conn)


async def initialize_db_connection():
    await DatabaseConnection.connect()

async def close_db_connection():
    await DatabaseConnection.disconnect()

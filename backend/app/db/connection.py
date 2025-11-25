
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
                        cls._pool = await asyncpg.create_pool(
                            user=os.getenv("DB_USER"),
                            password=os.getenv("DB_PASSWORD"),
                            host=os.getenv("DB_HOST"),
                            port=os.getenv("DB_PORT"),
                            database=os.getenv("DB_NAME"),
                            min_size=1,
                            max_size=10,
                        )
                        logger.info("Database connection pool created successfully.")
                    except Exception as e:
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
        return await cls._pool.acquire()

    @classmethod
    async def release_connection(cls, conn):
        if cls._pool and conn:
            await cls._pool.release(conn)


async def initialize_db_connection():
    await DatabaseConnection.connect()

async def close_db_connection():
    await DatabaseConnection.disconnect()

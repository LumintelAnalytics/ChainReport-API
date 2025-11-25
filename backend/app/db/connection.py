
import os
import asyncpg
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class DatabaseConnection:
    _pool = None

    @classmethod
    async def connect(cls):
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
                print("Database connection pool created successfully.")
            except Exception as e:
                print(f"Error connecting to the database: {e}")
                raise
        return cls._pool

    @classmethod
    async def disconnect(cls):
        if cls._pool:
            print("Closing database connection pool.")
            await cls._pool.close()
            cls._pool = None
            print("Database connection pool closed.")

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

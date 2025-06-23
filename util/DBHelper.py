import json

import asyncpg
from asyncpg.pool import Pool
from typing import Optional, List, Dict, Any, Union, AsyncIterator
from asyncpg import Record
from asyncpg.exceptions import PostgresError


class DBHelper:
    def __init__(self, dbname: str, dbpassword: str, dbhost: str = "localhost",
                 dbport: int = 5432, dbuser: str = "postgres"):
        self.conn_params = {
            "host": dbhost,
            "port": dbport,
            "database": dbname,
            "user": dbuser,
            "password": dbpassword
        }
        self.pool: Optional[Pool] = None

    async def initialize(self) -> None:
        """Initialize the connection pool"""
        self.pool = await asyncpg.create_pool(**self.conn_params)

    async def close(self) -> None:
        """Close the connection pool"""
        if self.pool:
            await self.pool.close()

    async def __aenter__(self) -> 'AsyncDBHelper':
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def execute(self, query: str, *args) -> str:
        """Execute a query without returning results"""
        async with self.pool.acquire() as conn:
            try:
                return await conn.execute(query, *args)
            except PostgresError as e:
                raise e

    async def fetch_one(self, query: str, *args) -> Optional[Record]:
        """Fetch a single row"""
        async with self.pool.acquire() as conn:
            try:
                return await conn.fetchrow(query, *args)
            except PostgresError as e:
                raise e

    async def fetch_all(self, query: str, *args) -> List[Record]:
        """Fetch all rows"""
        async with self.pool.acquire() as conn:
            try:
                return await conn.fetch(query, *args)
            except PostgresError as e:
                raise e

    async def insert_ad(self, data: Dict[str, Any]) -> str:
        """Insert a single ad with all its data"""
        city = data["address"][1] if data.get("address") else None

        query = """
            INSERT INTO info (
                link, city, address, price, photos, description, 
                factoids, summary, type, page, latitude, longitude, title
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            ON CONFLICT DO NOTHING
        """

        params = (
            data.get("link"),
            city,
            data.get("address"),
            data.get("price"),
            data.get("photos"),
            data.get("description"),
            json.dumps(data.get("factoids", {})),  # ← сериализуем
            json.dumps(data.get("summary", {})),  # ← сериализуем
            data.get("type"),
            data.get("page"),
            data.get("latitude"),
            data.get("longitude"),
            data.get("title")
        )

        async with self.pool.acquire() as conn:
            try:
                return await conn.execute(query, *params)
            except PostgresError as e:
                raise e
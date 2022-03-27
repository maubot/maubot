# maubot - A plugin-based Matrix bot system.
# Copyright (C) 2022 Tulir Asokan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from __future__ import annotations

from contextlib import asynccontextmanager
import asyncio

from mautrix.util.async_db import Database, PostgresDatabase, Scheme, UpgradeTable
from mautrix.util.async_db.connection import LoggingConnection
from mautrix.util.logging import TraceLogger

remove_double_quotes = str.maketrans({'"': "_"})


class ProxyPostgresDatabase(Database):
    scheme = Scheme.POSTGRES
    _underlying_pool: PostgresDatabase
    schema_name: str
    _quoted_schema: str
    _default_search_path: str
    _conn_sema: asyncio.Semaphore
    _max_conns: int

    def __init__(
        self,
        pool: PostgresDatabase,
        instance_id: str,
        max_conns: int,
        upgrade_table: UpgradeTable | None,
        log: TraceLogger | None = None,
    ) -> None:
        super().__init__(pool.url, upgrade_table=upgrade_table, log=log)
        self._underlying_pool = pool
        # Simple accidental SQL injection prevention.
        # Doesn't have to be perfect, since plugin instance IDs can only be set by admins anyway.
        self.schema_name = f"mbp_{instance_id.translate(remove_double_quotes)}"
        self._quoted_schema = f'"{self.schema_name}"'
        self._default_search_path = '"$user", public'
        self._conn_sema = asyncio.BoundedSemaphore(max_conns)
        self._max_conns = max_conns

    async def start(self) -> None:
        async with self._underlying_pool.acquire() as conn:
            self._default_search_path = await conn.fetchval("SHOW search_path")
            self.log.trace(f"Found default search path: {self._default_search_path}")
            await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {self._quoted_schema}")
        await super().start()

    async def stop(self) -> None:
        for _ in range(self._max_conns):
            try:
                await asyncio.wait_for(self._conn_sema.acquire(), timeout=3)
            except asyncio.TimeoutError:
                self.log.warning(
                    "Failed to drain plugin database connection pool, "
                    "the plugin may be leaking database connections"
                )
                break

    async def delete(self) -> None:
        self.log.info(f"Deleting schema {self.schema_name} and all data in it")
        try:
            await self._underlying_pool.execute(
                f"DROP SCHEMA IF EXISTS {self._quoted_schema} CASCADE"
            )
        except Exception:
            self.log.warning("Failed to delete schema", exc_info=True)

    @asynccontextmanager
    async def acquire(self) -> LoggingConnection:
        conn: LoggingConnection
        async with self._conn_sema, self._underlying_pool.acquire() as conn:
            await conn.execute(f"SET search_path = {self._quoted_schema}")
            try:
                yield conn
            finally:
                if not conn.wrapped.is_closed():
                    try:
                        await conn.execute(f"SET search_path = {self._default_search_path}")
                    except Exception:
                        self.log.exception("Error resetting search_path after use")
                        await conn.wrapped.close()
                else:
                    self.log.debug("Connection was closed after use, not resetting search_path")


__all__ = ["ProxyPostgresDatabase"]

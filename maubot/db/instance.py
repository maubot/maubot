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

from typing import TYPE_CHECKING, ClassVar
from enum import Enum

from asyncpg import Record
from attr import dataclass

from mautrix.types import UserID
from mautrix.util.async_db import Database

fake_db = Database.create("") if TYPE_CHECKING else None


class DatabaseEngine(Enum):
    SQLITE = "sqlite"
    POSTGRES = "postgres"


@dataclass
class Instance:
    db: ClassVar[Database] = fake_db

    id: str
    type: str
    enabled: bool
    primary_user: UserID
    config_str: str
    database_engine: DatabaseEngine | None

    @property
    def database_engine_str(self) -> str | None:
        return self.database_engine.value if self.database_engine else None

    @classmethod
    def _from_row(cls, row: Record | None) -> Instance | None:
        if row is None:
            return None
        data = {**row}
        db_engine = data.pop("database_engine", None)
        return cls(**data, database_engine=DatabaseEngine(db_engine) if db_engine else None)

    _columns = "id, type, enabled, primary_user, config, database_engine"

    @classmethod
    async def all(cls) -> list[Instance]:
        q = f"SELECT {cls._columns} FROM instance"
        rows = await cls.db.fetch(q)
        return [cls._from_row(row) for row in rows]

    @classmethod
    async def get(cls, id: str) -> Instance | None:
        q = f"SELECT {cls._columns} FROM instance WHERE id=$1"
        return cls._from_row(await cls.db.fetchrow(q, id))

    async def update_id(self, new_id: str) -> None:
        await self.db.execute("UPDATE instance SET id=$1 WHERE id=$2", new_id, self.id)
        self.id = new_id

    @property
    def _values(self):
        return (
            self.id,
            self.type,
            self.enabled,
            self.primary_user,
            self.config_str,
            self.database_engine_str,
        )

    async def insert(self) -> None:
        q = (
            "INSERT INTO instance (id, type, enabled, primary_user, config, database_engine) "
            "VALUES ($1, $2, $3, $4, $5, $6)"
        )
        await self.db.execute(q, *self._values)

    async def update(self) -> None:
        q = """
        UPDATE instance SET type=$2, enabled=$3, primary_user=$4, config=$5, database_engine=$6
        WHERE id=$1
        """
        await self.db.execute(q, *self._values)

    async def delete(self) -> None:
        await self.db.execute("DELETE FROM instance WHERE id=$1", self.id)

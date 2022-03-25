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

from mautrix.util.async_db import Connection, Scheme

from . import upgrade_table

legacy_version_query = "SELECT version_num FROM alembic_version"
last_legacy_version = "90aa88820eab"


@upgrade_table.register(description="Initial asyncpg revision")
async def upgrade_v1(conn: Connection, scheme: Scheme) -> None:
    if await conn.table_exists("alembic_version"):
        await migrate_legacy_to_v1(conn, scheme)
    else:
        return await create_v1_tables(conn)


async def create_v1_tables(conn: Connection) -> None:
    await conn.execute(
        """CREATE TABLE client (
            id           TEXT    PRIMARY KEY,
            homeserver   TEXT    NOT NULL,
            access_token TEXT    NOT NULL,
            device_id    TEXT    NOT NULL,
            enabled      BOOLEAN NOT NULL,

            next_batch TEXT NOT NULL,
            filter_id  TEXT NOT NULL,

            sync     BOOLEAN NOT NULL,
            autojoin BOOLEAN NOT NULL,
            online   BOOLEAN NOT NULL,

            displayname TEXT NOT NULL,
            avatar_url  TEXT NOT NULL
        )"""
    )
    await conn.execute(
        """CREATE TABLE instance (
            id           TEXT    PRIMARY KEY,
            type         TEXT    NOT NULL,
            enabled      BOOLEAN NOT NULL,
            primary_user TEXT    NOT NULL,
            config       TEXT    NOT NULL,
            FOREIGN KEY (primary_user) REFERENCES client(id) ON DELETE RESTRICT ON UPDATE CASCADE
        )"""
    )


async def migrate_legacy_to_v1(conn: Connection, scheme: Scheme) -> None:
    legacy_version = await conn.fetchval(legacy_version_query)
    if legacy_version != last_legacy_version:
        raise RuntimeError(
            "Legacy database is not on last version. "
            "Please upgrade the old database with alembic or drop it completely first."
        )
    await conn.execute("ALTER TABLE plugin RENAME TO instance")
    await update_state_store(conn, scheme)
    if scheme != Scheme.SQLITE:
        await varchar_to_text(conn)
    await conn.execute("DROP TABLE alembic_version")


async def update_state_store(conn: Connection, scheme: Scheme) -> None:
    # The Matrix state store already has more or less the correct schema, so set the version
    await conn.execute("CREATE TABLE mx_version (version INTEGER PRIMARY KEY)")
    await conn.execute("INSERT INTO mx_version (version) VALUES (2)")
    if scheme != Scheme.SQLITE:
        # Remove old uppercase membership type and recreate it as lowercase
        await conn.execute("ALTER TABLE mx_user_profile ALTER COLUMN membership TYPE TEXT")
        await conn.execute("DROP TYPE IF EXISTS membership")
        await conn.execute(
            "CREATE TYPE membership AS ENUM ('join', 'leave', 'invite', 'ban', 'knock')"
        )
        await conn.execute(
            "ALTER TABLE mx_user_profile ALTER COLUMN membership TYPE membership "
            "USING LOWER(membership)::membership"
        )
    else:
        # Recreate table to remove CHECK constraint and lowercase everything
        await conn.execute(
            """CREATE TABLE new_mx_user_profile (
                room_id     TEXT,
                user_id     TEXT,
                membership  TEXT NOT NULL
                            CHECK (membership IN ('join', 'leave', 'invite', 'ban', 'knock')),
                displayname TEXT,
                avatar_url  TEXT,
                PRIMARY KEY (room_id, user_id)
            )"""
        )
        await conn.execute(
            """
            INSERT INTO new_mx_user_profile (room_id, user_id, membership, displayname, avatar_url)
            SELECT room_id, user_id, LOWER(membership), displayname, avatar_url
            FROM mx_user_profile
            """
        )
        await conn.execute("DROP TABLE mx_user_profile")
        await conn.execute("ALTER TABLE new_mx_user_profile RENAME TO mx_user_profile")


async def varchar_to_text(conn: Connection) -> None:
    columns_to_adjust = {
        "client": (
            "id",
            "homeserver",
            "device_id",
            "next_batch",
            "filter_id",
            "displayname",
            "avatar_url",
        ),
        "instance": ("id", "type", "primary_user"),
        "mx_room_state": ("room_id",),
        "mx_user_profile": ("room_id", "user_id", "displayname", "avatar_url"),
    }
    for table, columns in columns_to_adjust.items():
        for column in columns:
            await conn.execute(f'ALTER TABLE "{table}" ALTER COLUMN {column} TYPE TEXT')

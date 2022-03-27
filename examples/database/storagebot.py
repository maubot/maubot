from __future__ import annotations

from mautrix.util.async_db import UpgradeTable, Connection
from maubot import Plugin, MessageEvent
from maubot.handlers import command

upgrade_table = UpgradeTable()


@upgrade_table.register(description="Initial revision")
async def upgrade_v1(conn: Connection) -> None:
    await conn.execute(
        """CREATE TABLE stored_data (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )"""
    )


@upgrade_table.register(description="Remember user who added value")
async def upgrade_v2(conn: Connection) -> None:
    await conn.execute("ALTER TABLE stored_data ADD COLUMN creator TEXT")


class StorageBot(Plugin):
    @command.new()
    async def storage(self, evt: MessageEvent) -> None:
        pass

    @storage.subcommand(help="Store a value")
    @command.argument("key")
    @command.argument("value", pass_raw=True)
    async def put(self, evt: MessageEvent, key: str, value: str) -> None:
        q = """
            INSERT INTO stored_data (key, value, creator) VALUES ($1, $2, $3)
            ON CONFLICT (key) DO UPDATE SET value=excluded.value, creator=excluded.creator
        """
        await self.database.execute(q, key, value, evt.sender)
        await evt.reply(f"Inserted {key} into the database")

    @storage.subcommand(help="Get a value from the storage")
    @command.argument("key")
    async def get(self, evt: MessageEvent, key: str) -> None:
        q = "SELECT key, value, creator FROM stored_data WHERE LOWER(key)=LOWER($1)"
        row = await self.database.fetchrow(q, key)
        if row:
            key = row["key"]
            value = row["value"]
            creator = row["creator"]
            await evt.reply(f"`{key}` stored by {creator}:\n\n```\n{value}\n```")
        else:
            await evt.reply(f"No data stored under `{key}` :(")

    @storage.subcommand(help="List keys in the storage")
    @command.argument("prefix", required=False)
    async def list(self, evt: MessageEvent, prefix: str | None) -> None:
        q = "SELECT key, creator FROM stored_data WHERE key LIKE $1"
        rows = await self.database.fetch(q, prefix + "%")
        prefix_reply = f" starting with `{prefix}`" if prefix else ""
        if len(rows) == 0:
            await evt.reply(f"Nothing{prefix_reply} stored in database :(")
        else:
            formatted_data = "\n".join(
                f"* `{row['key']}` stored by {row['creator']}" for row in rows
            )
            await evt.reply(
                f"Found {len(rows)} keys{prefix_reply} in database:\n\n{formatted_data}"
            )

    @classmethod
    def get_db_upgrade_table(cls) -> UpgradeTable | None:
        return upgrade_table

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

import asyncio
import sys

from mautrix.util.async_db import Database, DatabaseException, PostgresDatabase, Scheme
from mautrix.util.program import Program

from .__meta__ import __version__
from .client import Client
from .config import Config
from .db import init as init_db, upgrade_table
from .instance import PluginInstance
from .lib.future_awaitable import FutureAwaitable
from .lib.state_store import PgStateStore
from .loader.zip import init as init_zip_loader
from .management.api import init as init_mgmt_api
from .server import MaubotServer

try:
    from mautrix.crypto.store import PgCryptoStore
except ImportError:
    PgCryptoStore = None


class Maubot(Program):
    config: Config
    server: MaubotServer
    db: Database
    crypto_db: Database | None
    plugin_postgres_db: PostgresDatabase | None
    state_store: PgStateStore

    config_class = Config
    module = "maubot"
    name = "maubot"
    version = __version__
    command = "python -m maubot"
    description = "A plugin-based Matrix bot system."

    def prepare_log_websocket(self) -> None:
        from .management.api.log import init, stop_all

        init(self.loop)
        self.add_shutdown_actions(FutureAwaitable(stop_all))

    def prepare_arg_parser(self) -> None:
        super().prepare_arg_parser()
        self.parser.add_argument(
            "--ignore-unsupported-database",
            action="store_true",
            help="Run even if the database schema is too new",
        )
        self.parser.add_argument(
            "--ignore-foreign-tables",
            action="store_true",
            help="Run even if the database contains tables from other programs (like Synapse)",
        )

    def prepare_db(self) -> None:
        self.db = Database.create(
            self.config["database"],
            upgrade_table=upgrade_table,
            db_args=self.config["database_opts"],
            owner_name=self.name,
            ignore_foreign_tables=self.args.ignore_foreign_tables,
        )
        init_db(self.db)

        if self.config["crypto_database"] == "default":
            self.crypto_db = self.db
        else:
            self.crypto_db = Database.create(
                self.config["crypto_database"],
                upgrade_table=PgCryptoStore.upgrade_table,
                ignore_foreign_tables=self.args.ignore_foreign_tables,
            )

        if self.config["plugin_databases.postgres"] == "default":
            if self.db.scheme != Scheme.POSTGRES:
                self.log.critical(
                    'Using "default" as the postgres plugin database URL is only allowed if '
                    "the default database is postgres."
                )
                sys.exit(24)
            assert isinstance(self.db, PostgresDatabase)
            self.plugin_postgres_db = self.db
        elif self.config["plugin_databases.postgres"]:
            plugin_db = Database.create(
                self.config["plugin_databases.postgres"],
                db_args={
                    **self.config["database_opts"],
                    **self.config["plugin_databases.postgres_opts"],
                },
            )
            if plugin_db.scheme != Scheme.POSTGRES:
                self.log.critical("The plugin postgres database URL must be a postgres database")
                sys.exit(24)
            assert isinstance(plugin_db, PostgresDatabase)
            self.plugin_postgres_db = plugin_db
        else:
            self.plugin_postgres_db = None

    def prepare(self) -> None:
        super().prepare()

        if self.config["api_features.log"]:
            self.prepare_log_websocket()

        init_zip_loader(self.config)
        self.prepare_db()
        Client.init_cls(self)
        PluginInstance.init_cls(self)
        management_api = init_mgmt_api(self.config, self.loop)
        self.server = MaubotServer(management_api, self.config, self.loop)
        self.state_store = PgStateStore(self.db)

    async def start_db(self) -> None:
        self.log.debug("Starting database...")
        ignore_unsupported = self.args.ignore_unsupported_database
        self.db.upgrade_table.allow_unsupported = ignore_unsupported
        self.state_store.upgrade_table.allow_unsupported = ignore_unsupported
        PgCryptoStore.upgrade_table.allow_unsupported = ignore_unsupported
        try:
            await self.db.start()
            await self.state_store.upgrade_table.upgrade(self.db)
            if self.plugin_postgres_db and self.plugin_postgres_db is not self.db:
                await self.plugin_postgres_db.start()
            if self.crypto_db and self.crypto_db is not self.db:
                await self.crypto_db.start()
            else:
                await PgCryptoStore.upgrade_table.upgrade(self.db)
        except DatabaseException as e:
            self.log.critical("Failed to initialize database", exc_info=e)
            if e.explanation:
                self.log.info(e.explanation)
            sys.exit(25)

    async def system_exit(self) -> None:
        if hasattr(self, "db"):
            self.log.trace("Stopping database due to SystemExit")
            await self.db.stop()

    async def start(self) -> None:
        await self.start_db()
        await asyncio.gather(*[plugin.load() async for plugin in PluginInstance.all()])
        await asyncio.gather(*[client.start() async for client in Client.all()])
        await super().start()
        async for plugin in PluginInstance.all():
            await plugin.load()
        await self.server.start()

    async def stop(self) -> None:
        self.add_shutdown_actions(*(client.stop() for client in Client.cache.values()))
        await super().stop()
        self.log.debug("Stopping server")
        try:
            await asyncio.wait_for(self.server.stop(), 5)
        except asyncio.TimeoutError:
            self.log.warning("Stopping server timed out")
        await self.db.stop()


Maubot().run()

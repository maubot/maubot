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

from typing import TYPE_CHECKING, Any, AsyncGenerator, AsyncIterable, Awaitable, cast
from collections import defaultdict
import asyncio
import inspect
import io
import logging
import os.path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
import sqlalchemy as sql

from mautrix.types import UserID
from mautrix.util.async_getter_lock import async_getter_lock
from mautrix.util.config import BaseProxyConfig, RecursiveDict

from .client import Client
from .db import Instance as DBInstance
from .loader import PluginLoader, ZippedPluginLoader
from .plugin_base import Plugin

if TYPE_CHECKING:
    from .__main__ import Maubot
    from .server import PluginWebApp

log = logging.getLogger("maubot.instance")

yaml = YAML()
yaml.indent(4)
yaml.width = 200


class PluginInstance(DBInstance):
    maubot: "Maubot" = None
    cache: dict[str, PluginInstance] = {}
    plugin_directories: list[str] = []
    _async_get_locks: dict[Any, asyncio.Lock] = defaultdict(lambda: asyncio.Lock())

    log: logging.Logger
    loader: PluginLoader | None
    client: Client | None
    plugin: Plugin | None
    config: BaseProxyConfig | None
    base_cfg: RecursiveDict[CommentedMap] | None
    base_cfg_str: str | None
    inst_db: sql.engine.Engine | None
    inst_db_tables: dict[str, sql.Table] | None
    inst_webapp: PluginWebApp | None
    inst_webapp_url: str | None
    started: bool

    def __init__(
        self, id: str, type: str, enabled: bool, primary_user: UserID, config: str = ""
    ) -> None:
        super().__init__(
            id=id, type=type, enabled=bool(enabled), primary_user=primary_user, config_str=config
        )

    def __hash__(self) -> int:
        return hash(self.id)

    @classmethod
    def init_cls(cls, maubot: "Maubot") -> None:
        cls.maubot = maubot

    def postinit(self) -> None:
        self.log = log.getChild(self.id)
        self.cache[self.id] = self
        self.config = None
        self.started = False
        self.loader = None
        self.client = None
        self.plugin = None
        self.inst_db = None
        self.inst_db_tables = None
        self.inst_webapp = None
        self.inst_webapp_url = None
        self.base_cfg = None
        self.base_cfg_str = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "enabled": self.enabled,
            "started": self.started,
            "primary_user": self.primary_user,
            "config": self.config_str,
            "base_config": self.base_cfg_str,
            "database": (
                self.inst_db is not None and self.maubot.config["api_features.instance_database"]
            ),
        }

    def get_db_tables(self) -> dict[str, sql.Table]:
        if not self.inst_db_tables:
            metadata = sql.MetaData()
            metadata.reflect(self.inst_db)
            self.inst_db_tables = metadata.tables
        return self.inst_db_tables

    async def load(self) -> bool:
        if not self.loader:
            try:
                self.loader = PluginLoader.find(self.type)
            except KeyError:
                self.log.error(f"Failed to find loader for type {self.type}")
                await self.update_enabled(False)
                return False
        if not self.client:
            self.client = await Client.get(self.primary_user)
            if not self.client:
                self.log.error(f"Failed to get client for user {self.primary_user}")
                await self.update_enabled(False)
                return False
        if self.loader.meta.database:
            self.enable_database()
        if self.loader.meta.webapp:
            self.enable_webapp()
        self.log.debug("Plugin instance dependencies loaded")
        self.loader.references.add(self)
        self.client.references.add(self)
        return True

    def enable_webapp(self) -> None:
        self.inst_webapp, self.inst_webapp_url = self.maubot.server.get_instance_subapp(self.id)

    def disable_webapp(self) -> None:
        self.maubot.server.remove_instance_webapp(self.id)
        self.inst_webapp = None
        self.inst_webapp_url = None

    def enable_database(self) -> None:
        db_path = os.path.join(self.maubot.config["plugin_directories.db"], self.id)
        self.inst_db = sql.create_engine(f"sqlite:///{db_path}.db")

    async def delete(self) -> None:
        if self.loader is not None:
            self.loader.references.remove(self)
        if self.client is not None:
            self.client.references.remove(self)
        try:
            del self.cache[self.id]
        except KeyError:
            pass
        await super().delete()
        if self.inst_db:
            self.inst_db.dispose()
            ZippedPluginLoader.trash(
                os.path.join(self.maubot.config["plugin_directories.db"], f"{self.id}.db"),
                reason="deleted",
            )
        if self.inst_webapp:
            self.disable_webapp()

    def load_config(self) -> CommentedMap:
        return yaml.load(self.config_str)

    def save_config(self, data: RecursiveDict[CommentedMap]) -> None:
        buf = io.StringIO()
        yaml.dump(data, buf)
        self.config_str = buf.getvalue()

    async def start(self) -> None:
        if self.started:
            self.log.warning("Ignoring start() call to already started plugin")
            return
        elif not self.enabled:
            self.log.warning("Plugin disabled, not starting.")
            return
        if not self.client or not self.loader:
            self.log.warning("Missing plugin instance dependencies, attempting to load...")
            if not await self.load():
                return
        cls = await self.loader.load()
        if self.loader.meta.webapp and self.inst_webapp is None:
            self.log.debug("Enabling webapp after plugin meta reload")
            self.enable_webapp()
        elif not self.loader.meta.webapp and self.inst_webapp is not None:
            self.log.debug("Disabling webapp after plugin meta reload")
            self.disable_webapp()
        if self.loader.meta.database and self.inst_db is None:
            self.log.debug("Enabling database after plugin meta reload")
            self.enable_database()
        config_class = cls.get_config_class()
        if config_class:
            try:
                base = await self.loader.read_file("base-config.yaml")
                self.base_cfg = RecursiveDict(yaml.load(base.decode("utf-8")), CommentedMap)
                buf = io.StringIO()
                yaml.dump(self.base_cfg._data, buf)
                self.base_cfg_str = buf.getvalue()
            except (FileNotFoundError, KeyError):
                self.base_cfg = None
                self.base_cfg_str = None
            if self.base_cfg:
                base_cfg_func = self.base_cfg.clone
            else:

                def base_cfg_func() -> None:
                    return None

            self.config = config_class(self.load_config, base_cfg_func, self.save_config)
        self.plugin = cls(
            client=self.client.client,
            loop=self.maubot.loop,
            http=self.client.http_client,
            instance_id=self.id,
            log=self.log,
            config=self.config,
            database=self.inst_db,
            loader=self.loader,
            webapp=self.inst_webapp,
            webapp_url=self.inst_webapp_url,
        )
        try:
            await self.plugin.internal_start()
        except Exception:
            self.log.exception("Failed to start instance")
            await self.update_enabled(False)
            return
        self.started = True
        self.inst_db_tables = None
        self.log.info(
            f"Started instance of {self.loader.meta.id} v{self.loader.meta.version} "
            f"with user {self.client.id}"
        )

    async def stop(self) -> None:
        if not self.started:
            self.log.warning("Ignoring stop() call to non-running plugin")
            return
        self.log.debug("Stopping plugin instance...")
        self.started = False
        try:
            await self.plugin.internal_stop()
        except Exception:
            self.log.exception("Failed to stop instance")
        self.plugin = None
        self.inst_db_tables = None

    async def update_id(self, new_id: str | None) -> None:
        if new_id is not None and new_id.lower() != self.id:
            await super().update_id(new_id.lower())

    async def update_config(self, config: str | None) -> None:
        if config is None or self.config_str == config:
            return
        self.config_str = config
        if self.started and self.plugin is not None:
            res = self.plugin.on_external_config_update()
            if inspect.isawaitable(res):
                await res
        await self.update()

    async def update_primary_user(self, primary_user: UserID | None) -> bool:
        if primary_user is None or primary_user == self.primary_user:
            return True
        client = await Client.get(primary_user)
        if not client:
            return False
        await self.stop()
        self.primary_user = client.id
        if self.client:
            self.client.references.remove(self)
        self.client = client
        self.client.references.add(self)
        await self.update()
        await self.start()
        self.log.debug(f"Primary user switched to {self.client.id}")
        return True

    async def update_type(self, type: str | None) -> bool:
        if type is None or type == self.type:
            return True
        try:
            loader = PluginLoader.find(type)
        except KeyError:
            return False
        await self.stop()
        self.type = loader.meta.id
        if self.loader:
            self.loader.references.remove(self)
        self.loader = loader
        self.loader.references.add(self)
        await self.update()
        await self.start()
        self.log.debug(f"Type switched to {self.loader.meta.id}")
        return True

    async def update_started(self, started: bool) -> None:
        if started is not None and started != self.started:
            await (self.start() if started else self.stop())

    async def update_enabled(self, enabled: bool) -> None:
        if enabled is not None and enabled != self.enabled:
            self.enabled = enabled
            await self.update()

    @classmethod
    @async_getter_lock
    async def get(
        cls, instance_id: str, *, type: str | None = None, primary_user: UserID | None = None
    ) -> PluginInstance | None:
        try:
            return cls.cache[instance_id]
        except KeyError:
            pass

        instance = cast(cls, await super().get(instance_id))
        if instance is not None:
            instance.postinit()
            return instance

        if type and primary_user:
            instance = cls(instance_id, type=type, enabled=True, primary_user=primary_user)
            await instance.insert()
            instance.postinit()
            return instance

        return None

    @classmethod
    async def all(cls) -> AsyncGenerator[PluginInstance, None]:
        instances = await super().all()
        instance: PluginInstance
        for instance in instances:
            try:
                yield cls.cache[instance.id]
            except KeyError:
                instance.postinit()
                yield instance

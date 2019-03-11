# maubot - A plugin-based Matrix bot system.
# Copyright (C) 2018 Tulir Asokan
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
from typing import Dict, List, Optional, TYPE_CHECKING
from asyncio import AbstractEventLoop
from aiohttp import web
import os.path
import logging
import io

from ruamel.yaml.comments import CommentedMap
from ruamel.yaml import YAML
from sqlalchemy.orm import Session
import sqlalchemy as sql

from mautrix.util.config import BaseProxyConfig, RecursiveDict
from mautrix.types import UserID

from .db import DBPlugin
from .config import Config
from .client import Client
from .loader import PluginLoader, ZippedPluginLoader
from .plugin_base import Plugin

if TYPE_CHECKING:
    from .server import MaubotServer, PluginWebApp

log = logging.getLogger("maubot.instance")

yaml = YAML()
yaml.indent(4)


class PluginInstance:
    db: Session = None
    webserver: 'MaubotServer' = None
    mb_config: Config = None
    loop: AbstractEventLoop = None
    cache: Dict[str, 'PluginInstance'] = {}
    plugin_directories: List[str] = []

    log: logging.Logger
    loader: PluginLoader
    client: Client
    plugin: Plugin
    config: BaseProxyConfig
    base_cfg: RecursiveDict[CommentedMap]
    inst_db: sql.engine.Engine
    inst_db_tables: Dict[str, sql.Table]
    inst_webapp: 'PluginWebApp'
    inst_webapp_url: str
    started: bool

    def __init__(self, db_instance: DBPlugin):
        self.db_instance = db_instance
        self.log = log.getChild(self.id)
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
        self.cache[self.id] = self

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "enabled": self.enabled,
            "started": self.started,
            "primary_user": self.primary_user,
            "config": self.db_instance.config,
            "database": (self.inst_db is not None
                         and self.mb_config["api_features.instance_database"]),
        }

    def get_db_tables(self) -> Dict[str, sql.Table]:
        if not self.inst_db_tables:
            metadata = sql.MetaData()
            metadata.reflect(self.inst_db)
            self.inst_db_tables = metadata.tables
        return self.inst_db_tables

    def load(self) -> bool:
        if not self.loader:
            try:
                self.loader = PluginLoader.find(self.type)
            except KeyError:
                self.log.error(f"Failed to find loader for type {self.type}")
                self.db_instance.enabled = False
                return False
        if not self.client:
            self.client = Client.get(self.primary_user)
            if not self.client:
                self.log.error(f"Failed to get client for user {self.primary_user}")
                self.db_instance.enabled = False
                return False
        if self.loader.meta.database:
            db_path = os.path.join(self.mb_config["plugin_directories.db"], self.id)
            self.inst_db = sql.create_engine(f"sqlite:///{db_path}.db")
        if self.loader.meta.webapp:
            self.inst_webapp, self.inst_webapp_url = self.webserver.get_instance_subapp(self.id)
        self.log.debug("Plugin instance dependencies loaded")
        self.loader.references.add(self)
        self.client.references.add(self)
        return True

    def delete(self) -> None:
        if self.loader is not None:
            self.loader.references.remove(self)
        if self.client is not None:
            self.client.references.remove(self)
        try:
            del self.cache[self.id]
        except KeyError:
            pass
        self.db.delete(self.db_instance)
        self.db.commit()
        if self.inst_db:
            self.inst_db.dispose()
            ZippedPluginLoader.trash(
                os.path.join(self.mb_config["plugin_directories.db"], f"{self.id}.db"),
                reason="deleted")
        if self.inst_webapp:
            self.webserver.remove_instance_webapp(self.id)

    def load_config(self) -> CommentedMap:
        return yaml.load(self.db_instance.config)

    def save_config(self, data: RecursiveDict[CommentedMap]) -> None:
        buf = io.StringIO()
        yaml.dump(data, buf)
        self.db_instance.config = buf.getvalue()

    async def start(self) -> None:
        if self.started:
            self.log.warning("Ignoring start() call to already started plugin")
            return
        elif not self.enabled:
            self.log.warning("Plugin disabled, not starting.")
            return
        if not self.client or not self.loader:
            self.log.warning("Missing plugin instance dependencies, attempting to load...")
            if not self.load():
                return
        cls = await self.loader.load()
        config_class = cls.get_config_class()
        if config_class:
            try:
                base = await self.loader.read_file("base-config.yaml")
                self.base_cfg = RecursiveDict(yaml.load(base.decode("utf-8")), CommentedMap)
            except (FileNotFoundError, KeyError):
                self.base_cfg = None
            self.config = config_class(self.load_config, lambda: self.base_cfg, self.save_config)
        self.plugin = cls(client=self.client.client, loop=self.loop, http=self.client.http_client,
                          instance_id=self.id, log=self.log, config=self.config,
                          database=self.inst_db, webapp=self.inst_webapp,
                          webapp_url=self.inst_webapp_url)
        try:
            await self.plugin.start()
        except Exception:
            self.log.exception("Failed to start instance")
            self.db_instance.enabled = False
            return
        self.started = True
        self.inst_db_tables = None
        self.log.info(f"Started instance of {self.loader.meta.id} v{self.loader.meta.version} "
                      f"with user {self.client.id}")

    async def stop(self) -> None:
        if not self.started:
            self.log.warning("Ignoring stop() call to non-running plugin")
            return
        self.log.debug("Stopping plugin instance...")
        self.started = False
        try:
            await self.plugin.stop()
        except Exception:
            self.log.exception("Failed to stop instance")
        self.plugin = None
        self.inst_db_tables = None

    @classmethod
    def get(cls, instance_id: str, db_instance: Optional[DBPlugin] = None
            ) -> Optional['PluginInstance']:
        try:
            return cls.cache[instance_id]
        except KeyError:
            db_instance = db_instance or DBPlugin.query.get(instance_id)
            if not db_instance:
                return None
            return PluginInstance(db_instance)

    @classmethod
    def all(cls) -> List['PluginInstance']:
        return [cls.get(plugin.id, plugin) for plugin in DBPlugin.query.all()]

    def update_id(self, new_id: str) -> None:
        if new_id is not None and new_id != self.id:
            self.db_instance.id = new_id

    def update_config(self, config: str) -> None:
        if not config or self.db_instance.config == config:
            return
        self.db_instance.config = config
        if self.started and self.plugin is not None:
            self.plugin.on_external_config_update()

    async def update_primary_user(self, primary_user: UserID) -> bool:
        if not primary_user or primary_user == self.primary_user:
            return True
        client = Client.get(primary_user)
        if not client:
            return False
        await self.stop()
        self.db_instance.primary_user = client.id
        if self.client:
            self.client.references.remove(self)
        self.client = client
        self.client.references.add(self)
        await self.start()
        self.log.debug(f"Primary user switched to {self.client.id}")
        return True

    async def update_type(self, type: str) -> bool:
        if not type or type == self.type:
            return True
        try:
            loader = PluginLoader.find(type)
        except KeyError:
            return False
        await self.stop()
        self.db_instance.type = loader.meta.id
        if self.loader:
            self.loader.references.remove(self)
        self.loader = loader
        self.loader.references.add(self)
        await self.start()
        self.log.debug(f"Type switched to {self.loader.meta.id}")
        return True

    async def update_started(self, started: bool) -> None:
        if started is not None and started != self.started:
            await (self.start() if started else self.stop())

    def update_enabled(self, enabled: bool) -> None:
        if enabled is not None and enabled != self.enabled:
            self.db_instance.enabled = enabled

    # region Properties

    @property
    def id(self) -> str:
        return self.db_instance.id

    @id.setter
    def id(self, value: str) -> None:
        self.db_instance.id = value

    @property
    def type(self) -> str:
        return self.db_instance.type

    @property
    def enabled(self) -> bool:
        return self.db_instance.enabled

    @property
    def primary_user(self) -> UserID:
        return self.db_instance.primary_user

    # endregion


def init(db: Session, config: Config, webserver: 'MaubotServer', loop: AbstractEventLoop) -> List[
    PluginInstance]:
    PluginInstance.db = db
    PluginInstance.mb_config = config
    PluginInstance.loop = loop
    PluginInstance.webserver = webserver
    return PluginInstance.all()

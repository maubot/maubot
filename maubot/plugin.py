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
from typing import Dict, List, Optional
from ruamel.yaml.comments import CommentedMap
from ruamel.yaml import YAML
import logging
import io

from mautrix.util import BaseProxyConfig, RecursiveDict
from mautrix.types import UserID

from .db import DBPlugin
from .config import Config
from .client import Client
from .loader import PluginLoader
from .plugin_base import Plugin

log = logging.getLogger("maubot.plugin")

yaml = YAML()
yaml.indent(4)


class PluginInstance:
    mb_config: Config = None
    cache: Dict[str, 'PluginInstance'] = {}
    plugin_directories: List[str] = []

    log: logging.Logger
    loader: PluginLoader
    client: Client
    plugin: Plugin
    config: BaseProxyConfig

    def __init__(self, db_instance: DBPlugin):
        self.db_instance = db_instance
        self.log = logging.getLogger(f"maubot.plugin.{self.id}")
        self.config = None
        self.cache[self.id] = self

    def load(self) -> None:
        try:
            self.loader = PluginLoader.find(self.type)
        except KeyError:
            self.log.error(f"Failed to find loader for type {self.type}")
            self.enabled = False
            return
        self.client = Client.get(self.primary_user)
        if not self.client:
            self.log.error(f"Failed to get client for user {self.primary_user}")
            self.enabled = False
        self.log.debug("Plugin instance dependencies loaded")

    def load_config(self) -> CommentedMap:
        return yaml.load(self.db_instance.config)

    def load_config_base(self) -> Optional[RecursiveDict[CommentedMap]]:
        try:
            base = self.loader.read_file("base-config.yaml")
            return RecursiveDict(yaml.load(base.decode("utf-8")), CommentedMap)
        except (FileNotFoundError, KeyError):
            return None

    def save_config(self, data: RecursiveDict[CommentedMap]) -> None:
        buf = io.StringIO()
        yaml.dump(data, buf)
        self.db_instance.config = buf.getvalue()

    async def start(self) -> None:
        if not self.enabled:
            self.log.warning(f"Plugin disabled, not starting.")
            return
        cls = self.loader.load()
        config_class = cls.get_config_class()
        if config_class:
            self.config = config_class(self.load_config, self.load_config_base,
                                       self.save_config)
        self.plugin = cls(self.client.client, self.id, self.log, self.config,
                          self.mb_config["plugin_db_directory"])
        self.loader.references |= {self}
        await self.plugin.start()
        self.log.info(f"Started instance of {self.loader.id} v{self.loader.version} "
                      f"with user {self.client.id}")

    async def stop(self) -> None:
        self.log.debug("Stopping plugin instance...")
        self.loader.references -= {self}
        await self.plugin.stop()
        self.plugin = None

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

    @type.setter
    def type(self, value: str) -> None:
        self.db_instance.type = value

    @property
    def enabled(self) -> bool:
        return self.db_instance.enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self.db_instance.enabled = value

    @property
    def primary_user(self) -> UserID:
        return self.db_instance.primary_user

    @primary_user.setter
    def primary_user(self, value: UserID) -> None:
        self.db_instance.primary_user = value

    # endregion


def init(config: Config):
    PluginInstance.mb_config = config

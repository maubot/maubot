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
import logging

from mautrix.types import UserID

from .db import DBPlugin
from .client import Client
from .loader import PluginLoader
from .plugin_base import Plugin

log = logging.getLogger("maubot.plugin")


class PluginInstance:
    cache: Dict[str, 'PluginInstance'] = {}
    plugin_directories: List[str] = []

    log: logging.Logger
    loader: PluginLoader
    client: Client
    plugin: Plugin

    def __init__(self, db_instance: DBPlugin):
        self.db_instance = db_instance
        self.log = logging.getLogger(f"maubot.plugin.{self.id}")
        self.cache[self.id] = self

    def load(self) -> None:
        try:
            self.loader = PluginLoader.find(self.type)
        except KeyError:
            self.log.error(f"Failed to find loader for type {self.type}")
            self.db_instance.enabled = False
            return
        self.client = Client.get(self.primary_user)
        if not self.client:
            self.log.error(f"Failed to get client for user {self.primary_user}")
            self.db_instance.enabled = False

    async def start(self) -> None:
        self.log.debug(f"Starting...")
        cls = self.loader.load()
        self.plugin = cls(self.client.client, self.id, self.log)
        self.loader.references |= {self}
        await self.plugin.start()

    async def stop(self) -> None:
        self.log.debug("Stopping...")
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

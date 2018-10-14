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
from typing import Dict, List
import logging

from mautrix.types import UserID

from .db import DBPlugin

log = logging.getLogger("maubot.plugin")


class PluginInstance:
    cache: Dict[str, 'PluginInstance'] = {}
    plugin_directories: List[str] = []

    def __init__(self, db_instance: DBPlugin):
        self.db_instance = db_instance
        self.cache[self.id] = self

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

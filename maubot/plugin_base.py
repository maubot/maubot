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
from typing import Type, Optional, TYPE_CHECKING
from logging import Logger
from abc import ABC, abstractmethod
import os.path

from sqlalchemy.engine.base import Engine
import sqlalchemy as sql

if TYPE_CHECKING:
    from .client import MaubotMatrixClient
    from .command_spec import CommandSpec
    from mautrix.util import BaseProxyConfig


class Plugin(ABC):
    client: 'MaubotMatrixClient'
    id: str
    log: Logger
    config: Optional['BaseProxyConfig']

    def __init__(self, client: 'MaubotMatrixClient', plugin_instance_id: str, log: Logger,
                 config: Optional['BaseProxyConfig'], db_base_path: str) -> None:
        self.client = client
        self.id = plugin_instance_id
        self.log = log
        self.config = config
        self.__db_base_path = db_base_path

    def request_db_engine(self) -> Engine:
        return sql.create_engine(f"sqlite:///{os.path.join(self.__db_base_path, self.id)}.db")

    def set_command_spec(self, spec: 'CommandSpec') -> None:
        self.client.set_command_spec(self.id, spec)

    @abstractmethod
    async def start(self) -> None:
        pass

    @abstractmethod
    async def stop(self) -> None:
        pass

    @classmethod
    def get_config_class(cls) -> Optional[Type['BaseProxyConfig']]:
        return None

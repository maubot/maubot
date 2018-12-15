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
from abc import ABC
from logging import Logger
from asyncio import AbstractEventLoop
import functools

from sqlalchemy.engine.base import Engine
from aiohttp import ClientSession

if TYPE_CHECKING:
    from mautrix.types import Event
    from mautrix.util.config import BaseProxyConfig
    from .client import MaubotMatrixClient


class Plugin(ABC):
    client: 'MaubotMatrixClient'
    id: str
    log: Logger
    loop: AbstractEventLoop
    config: Optional['BaseProxyConfig']
    database: Optional[Engine]

    def __init__(self, client: 'MaubotMatrixClient', loop: AbstractEventLoop, http: ClientSession,
                 instance_id: str, log: Logger, config: Optional['BaseProxyConfig'],
                 database: Optional[Engine]) -> None:
        self.client = client
        self.loop = loop
        self.http = http
        self.id = instance_id
        self.log = log
        self.config = config
        self.database = database
        self._handlers_at_startup = []

    async def start(self) -> None:
        for key in dir(self):
            val = getattr(self, key)
            if hasattr(val, "__mb_event_handler__"):
                handle_own_events = hasattr(val, "__mb_handle_own_events__")

                @functools.wraps(val)
                async def handler(event: Event) -> None:
                    if not handle_own_events and getattr(event, "sender", "") == self.client.mxid:
                        return
                    for filter in val.__mb_event_filters__:
                        if not filter(event):
                            return
                    await val(event)
                self._handlers_at_startup.append((handler, val.__mb_event_type__))
                self.client.add_event_handler(val.__mb_event_type__, handler)

    async def stop(self) -> None:
        for func, event_type in self._handlers_at_startup:
            self.client.remove_event_handler(event_type, func)

    @classmethod
    def get_config_class(cls) -> Optional[Type['BaseProxyConfig']]:
        return None

    def on_external_config_update(self) -> None:
        if self.config:
            self.config.load_and_update()

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
from typing import Dict, List, Optional, Union, Callable
from aiohttp import ClientSession
import asyncio
import logging

from mautrix import Client as MatrixClient
from mautrix.client import EventHandler
from mautrix.types import (UserID, SyncToken, FilterID, ContentURI, StateEvent, Membership,
                           EventType, MessageEvent)

from .command_spec import ParsedCommand
from .db import DBClient

log = logging.getLogger("maubot.client")


class MaubotMatrixClient(MatrixClient):
    def __init__(self, maubot_client: 'Client', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._maubot_client = maubot_client
        self.command_handlers: Dict[str, List[EventHandler]] = {}
        self.commands: List[ParsedCommand] = []

        self.add_event_handler(self._command_event_handler, EventType.ROOM_MESSAGE)

    async def _command_event_handler(self, evt: MessageEvent) -> None:
        for command in self.commands:
            if command.match(evt):
                await self._trigger_command(command, evt)
                return

    async def _trigger_command(self, command: ParsedCommand, evt: MessageEvent) -> None:
        for handler in self.command_handlers.get(command.name, []):
            await handler(evt)

    def on(self, var: Union[EventHandler, EventType, str]
           ) -> Union[EventHandler, Callable[[EventHandler], EventHandler]]:
        if isinstance(var, str):
            def decorator(func: EventHandler) -> EventHandler:
                self.add_command_handler(var, func)
                return func

            return decorator
        return super().on(var)

    def add_command_handler(self, command: str, handler: EventHandler) -> None:
        self.command_handlers.setdefault(command, []).append(handler)

    def remove_command_handler(self, command: str, handler: EventHandler) -> None:
        try:
            self.command_handlers[command].remove(handler)
        except (KeyError, ValueError):
            pass


class Client:
    cache: Dict[UserID, 'Client'] = {}
    http_client: ClientSession = None

    db_instance: DBClient
    client: MaubotMatrixClient

    def __init__(self, db_instance: DBClient) -> None:
        self.db_instance = db_instance
        self.cache[self.id] = self
        self.client = MaubotMatrixClient(maubot_client=self,
                                         store=self.db_instance,
                                         mxid=self.id,
                                         base_url=self.homeserver,
                                         token=self.access_token,
                                         client_session=self.http_client,
                                         log=log.getChild(self.id))
        if self.autojoin:
            self.client.add_event_handler(self._handle_invite, EventType.ROOM_MEMBER)

    @classmethod
    def get(cls, user_id: UserID) -> Optional['Client']:
        try:
            return cls.cache[user_id]
        except KeyError:
            db_instance = DBClient.query.get(user_id)
            if not db_instance:
                return None
            return Client(db_instance)

    # region Properties

    @property
    def id(self) -> UserID:
        return self.db_instance.id

    @property
    def homeserver(self) -> str:
        return self.db_instance.id

    @property
    def access_token(self) -> str:
        return self.db_instance.access_token

    @access_token.setter
    def access_token(self, value: str) -> None:
        self.client.api.token = value
        self.db_instance.access_token = value

    @property
    def next_batch(self) -> SyncToken:
        return self.db_instance.next_batch

    @next_batch.setter
    def next_batch(self, value: SyncToken) -> None:
        self.db_instance.next_batch = value

    @property
    def filter_id(self) -> FilterID:
        return self.db_instance.filter_id

    @filter_id.setter
    def filter_id(self, value: FilterID) -> None:
        self.db_instance.filter_id = value

    @property
    def sync(self) -> bool:
        return self.db_instance.sync

    @sync.setter
    def sync(self, value: bool) -> None:
        self.db_instance.sync = value

    @property
    def autojoin(self) -> bool:
        return self.db_instance.autojoin

    @autojoin.setter
    def autojoin(self, value: bool) -> None:
        if value == self.db_instance.autojoin:
            return
        if value:
            self.client.add_event_handler(self._handle_invite, EventType.ROOM_MEMBER)
        else:
            self.client.remove_event_handler(self._handle_invite, EventType.ROOM_MEMBER)
        self.db_instance.autojoin = value

    @property
    def displayname(self) -> str:
        return self.db_instance.displayname

    @displayname.setter
    def displayname(self, value: str) -> None:
        self.db_instance.displayname = value

    @property
    def avatar_url(self) -> ContentURI:
        return self.db_instance.avatar_url

    @avatar_url.setter
    def avatar_url(self, value: ContentURI) -> None:
        self.db_instance.avatar_url = value

    # endregion

    async def _handle_invite(self, evt: StateEvent) -> None:
        if evt.state_key == self.id and evt.content.membership == Membership.INVITE:
            await self.client.join_room_by_id(evt.room_id)

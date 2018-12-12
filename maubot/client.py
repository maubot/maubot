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
from typing import Dict, List, Optional, Set, TYPE_CHECKING
import asyncio
import logging

from sqlalchemy.orm import Session
from aiohttp import ClientSession

from mautrix.errors import MatrixInvalidToken, MatrixRequestError
from mautrix.types import (UserID, SyncToken, FilterID, ContentURI, StrippedStateEvent, Membership,
                           EventType, Filter, RoomFilter, RoomEventFilter)

from .db import DBClient
from .matrix import MaubotMatrixClient

if TYPE_CHECKING:
    from .instance import PluginInstance

log = logging.getLogger("maubot.client")


class Client:
    db: Session = None
    log: logging.Logger = None
    loop: asyncio.AbstractEventLoop = None
    cache: Dict[UserID, 'Client'] = {}
    http_client: ClientSession = None

    references: Set['PluginInstance']
    db_instance: DBClient
    client: MaubotMatrixClient
    started: bool

    def __init__(self, db_instance: DBClient) -> None:
        self.db_instance = db_instance
        self.cache[self.id] = self
        self.log = log.getChild(self.id)
        self.references = set()
        self.started = False
        self.client = MaubotMatrixClient(mxid=self.id, base_url=self.homeserver,
                                         token=self.access_token, client_session=self.http_client,
                                         log=self.log, loop=self.loop, store=self.db_instance)
        if self.autojoin:
            self.client.add_event_handler(self._handle_invite, EventType.ROOM_MEMBER)

    async def start(self, try_n: Optional[int] = 0) -> None:
        try:
            if try_n > 0:
                await asyncio.sleep(try_n * 10)
            await self._start(try_n)
        except Exception:
            self.log.exception("Failed to start")

    async def _start(self, try_n: Optional[int] = 0) -> None:
        if not self.enabled:
            self.log.debug("Not starting disabled client")
            return
        elif self.started:
            self.log.warning("Ignoring start() call to started client")
            return
        try:
            user_id = await self.client.whoami()
        except MatrixInvalidToken as e:
            self.log.error(f"Invalid token: {e}. Disabling client")
            self.db_instance.enabled = False
            return
        except MatrixRequestError:
            if try_n >= 5:
                self.log.exception("Failed to get /account/whoami, disabling client")
                self.db_instance.enabled = False
            else:
                self.log.exception(f"Failed to get /account/whoami, "
                                   f"retrying in {(try_n + 1) * 10}s")
                _ = asyncio.ensure_future(self.start(try_n + 1), loop=self.loop)
            return
        if user_id != self.id:
            self.log.error(f"User ID mismatch: expected {self.id}, but got {user_id}")
            self.db_instance.enabled = False
            return
        if not self.filter_id:
            self.db_instance.filter_id = await self.client.create_filter(Filter(
                room=RoomFilter(
                    timeline=RoomEventFilter(
                        limit=50,
                    ),
                ),
            ))
        if self.displayname != "disable":
            await self.client.set_displayname(self.displayname)
        if self.avatar_url != "disable":
            await self.client.set_avatar_url(self.avatar_url)
            self.start_sync()
        self.started = True
        self.log.info("Client started, starting plugin instances...")
        await self.start_plugins()

    async def start_plugins(self) -> None:
        await asyncio.gather(*[plugin.start() for plugin in self.references], loop=self.loop)

    async def stop_plugins(self) -> None:
        await asyncio.gather(*[plugin.stop() for plugin in self.references if plugin.started],
                             loop=self.loop)

    def start_sync(self) -> None:
        if self.sync:
            self.client.start(self.filter_id)

    def stop_sync(self) -> None:
        self.client.stop()

    async def stop(self) -> None:
        if self.started:
            self.started = False
            await self.stop_plugins()
            self.stop_sync()

    def delete(self) -> None:
        try:
            del self.cache[self.id]
        except KeyError:
            pass
        self.db.delete(self.db_instance)
        self.db.commit()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "homeserver": self.homeserver,
            "access_token": self.access_token,
            "enabled": self.enabled,
            "started": self.started,
            "sync": self.sync,
            "autojoin": self.autojoin,
            "displayname": self.displayname,
            "avatar_url": self.avatar_url,
            "instances": [instance.to_dict() for instance in self.references],
        }

    @classmethod
    def get(cls, user_id: UserID, db_instance: Optional[DBClient] = None) -> Optional['Client']:
        try:
            return cls.cache[user_id]
        except KeyError:
            db_instance = db_instance or DBClient.query.get(user_id)
            if not db_instance:
                return None
            return Client(db_instance)

    @classmethod
    def all(cls) -> List['Client']:
        return [cls.get(user.id, user) for user in DBClient.query.all()]

    async def _handle_invite(self, evt: StrippedStateEvent) -> None:
        if evt.state_key == self.id and evt.content.membership == Membership.INVITE:
            await self.client.join_room(evt.room_id)

    async def update_started(self, started: bool) -> None:
        if started is None or started == self.started:
            return
        if started:
            await self.start()
        else:
            await self.stop()

    async def update_displayname(self, displayname: str) -> None:
        if displayname is None or displayname == self.displayname:
            return
        self.db_instance.displayname = displayname
        await self.client.set_displayname(self.displayname)

    async def update_avatar_url(self, avatar_url: ContentURI) -> None:
        if avatar_url is None or avatar_url == self.avatar_url:
            return
        self.db_instance.avatar_url = avatar_url
        await self.client.set_avatar_url(self.avatar_url)

    async def update_access_details(self, access_token: str, homeserver: str) -> None:
        if not access_token and not homeserver:
            return
        elif access_token == self.access_token and homeserver == self.homeserver:
            return
        new_client = MaubotMatrixClient(mxid=self.id, base_url=homeserver or self.homeserver,
                                        token=access_token or self.access_token, loop=self.loop,
                                        client_session=self.http_client, log=self.log)
        mxid = await new_client.whoami()
        if mxid != self.id:
            raise ValueError(f"MXID mismatch: {mxid}")
        new_client.store = self.db_instance
        self.stop_sync()
        self.client = new_client
        self.db_instance.homeserver = homeserver
        self.db_instance.access_token = access_token
        self.start_sync()

    # region Properties

    @property
    def id(self) -> UserID:
        return self.db_instance.id

    @property
    def homeserver(self) -> str:
        return self.db_instance.homeserver

    @property
    def access_token(self) -> str:
        return self.db_instance.access_token

    @property
    def enabled(self) -> bool:
        return self.db_instance.enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self.db_instance.enabled = value

    @property
    def next_batch(self) -> SyncToken:
        return self.db_instance.next_batch

    @property
    def filter_id(self) -> FilterID:
        return self.db_instance.filter_id

    @property
    def sync(self) -> bool:
        return self.db_instance.sync

    @sync.setter
    def sync(self, value: bool) -> None:
        if value == self.db_instance.sync:
            return
        self.db_instance.sync = value
        if self.started:
            if value:
                self.start_sync()
            else:
                self.stop_sync()

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

    @property
    def avatar_url(self) -> ContentURI:
        return self.db_instance.avatar_url

    # endregion


def init(db: Session, loop: asyncio.AbstractEventLoop) -> List[Client]:
    Client.db = db
    Client.http_client = ClientSession(loop=loop)
    Client.loop = loop
    return Client.all()

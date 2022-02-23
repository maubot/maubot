# maubot - A plugin-based Matrix bot system.
# Copyright (C) 2021 Tulir Asokan
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
from typing import Dict, Iterable, Optional, Set, Callable, Any, Awaitable, Union, TYPE_CHECKING
import asyncio
import logging

from aiohttp import ClientSession

from mautrix.errors import MatrixInvalidToken
from mautrix.types import (UserID, SyncToken, FilterID, ContentURI, StrippedStateEvent, Membership,
                           StateEvent, EventType, Filter, RoomFilter, RoomEventFilter, EventFilter,
                           PresenceState, StateFilter, DeviceID)
from mautrix.client import InternalEventType
from mautrix.client.state_store.sqlalchemy import SQLStateStore as BaseSQLStateStore

from .lib.store_proxy import SyncStoreProxy
from .db import DBClient
from .matrix import MaubotMatrixClient

try:
    from mautrix.crypto import OlmMachine, StateStore as CryptoStateStore, PgCryptoStore
    from mautrix.util.async_db import Database as AsyncDatabase


    class SQLStateStore(BaseSQLStateStore, CryptoStateStore):
        pass


    crypto_import_error = None
except ImportError as e:
    OlmMachine = CryptoStateStore = PgCryptoStore = AsyncDatabase = None
    SQLStateStore = BaseSQLStateStore
    crypto_import_error = e

if TYPE_CHECKING:
    from .instance import PluginInstance
    from .config import Config

log = logging.getLogger("maubot.client")


class Client:
    log: logging.Logger = None
    loop: asyncio.AbstractEventLoop = None
    cache: Dict[UserID, 'Client'] = {}
    http_client: ClientSession = None
    global_state_store: Union['BaseSQLStateStore', 'CryptoStateStore'] = SQLStateStore()
    crypto_db: Optional['AsyncDatabase'] = None

    references: Set['PluginInstance']
    db_instance: DBClient
    client: MaubotMatrixClient
    crypto: Optional['OlmMachine']
    crypto_store: Optional['PgCryptoStore']
    started: bool

    remote_displayname: Optional[str]
    remote_avatar_url: Optional[ContentURI]

    def __init__(self, db_instance: DBClient) -> None:
        self.db_instance = db_instance
        self.cache[self.id] = self
        self.log = log.getChild(self.id)
        self.references = set()
        self.started = False
        self.sync_ok = True
        self.remote_displayname = None
        self.remote_avatar_url = None
        self.client = MaubotMatrixClient(mxid=self.id, base_url=self.homeserver,
                                         token=self.access_token, client_session=self.http_client,
                                         log=self.log, loop=self.loop, device_id=self.device_id,
                                         sync_store=SyncStoreProxy(self.db_instance),
                                         state_store=self.global_state_store)
        if self.enable_crypto:
            self._prepare_crypto()
        else:
            self.crypto_store = None
            self.crypto = None
        self.client.ignore_initial_sync = True
        self.client.ignore_first_sync = True
        self.client.presence = PresenceState.ONLINE if self.online else PresenceState.OFFLINE
        if self.autojoin:
            self.client.add_event_handler(EventType.ROOM_MEMBER, self._handle_invite)
        self.client.add_event_handler(EventType.ROOM_TOMBSTONE, self._handle_tombstone)
        self.client.add_event_handler(InternalEventType.SYNC_ERRORED, self._set_sync_ok(False))
        self.client.add_event_handler(InternalEventType.SYNC_SUCCESSFUL, self._set_sync_ok(True))

    @property
    def enable_crypto(self) -> bool:
        if not self.device_id:
            return False
        elif not OlmMachine:
            global crypto_import_error
            self.log.warning("Client has device ID, but encryption dependencies not installed",
                             exc_info=crypto_import_error)
            # Clear the stack trace after it's logged once to avoid spamming logs
            crypto_import_error = None
            return False
        elif not self.crypto_db:
            self.log.warning("Client has device ID, but crypto database is not prepared")
            return False
        return True

    def _prepare_crypto(self) -> None:
        self.crypto_store = PgCryptoStore(account_id=self.id, pickle_key="mau.crypto",
                                          db=self.crypto_db)
        self.crypto = OlmMachine(self.client, self.crypto_store, self.global_state_store)
        self.client.crypto = self.crypto

    def _remove_crypto_event_handlers(self) -> None:
        if not self.crypto:
            return
        handlers = [
            (InternalEventType.DEVICE_OTK_COUNT, self.crypto.handle_otk_count),
            (InternalEventType.DEVICE_LISTS, self.crypto.handle_device_lists),
            (EventType.TO_DEVICE_ENCRYPTED, self.crypto.handle_to_device_event),
            (EventType.ROOM_KEY_REQUEST, self.crypto.handle_room_key_request),
            (EventType.ROOM_MEMBER, self.crypto.handle_member_event),
        ]
        for event_type, func in handlers:
            self.client.remove_event_handler(event_type, func)

    def _set_sync_ok(self, ok: bool) -> Callable[[Dict[str, Any]], Awaitable[None]]:
        async def handler(data: Dict[str, Any]) -> None:
            self.sync_ok = ok

        return handler

    async def start(self, try_n: Optional[int] = 0) -> None:
        try:
            if try_n > 0:
                await asyncio.sleep(try_n * 10)
            await self._start(try_n)
        except Exception:
            self.log.exception("Failed to start")

    async def _start_crypto(self) -> None:
        self.log.debug("Enabling end-to-end encryption support")
        await self.crypto_store.open()
        crypto_device_id = await self.crypto_store.get_device_id()
        if crypto_device_id and crypto_device_id != self.device_id:
            self.log.warning("Mismatching device ID in crypto store and main database, "
                             "resetting encryption")
            await self.crypto_store.delete()
            crypto_device_id = None
        await self.crypto.load()
        if not crypto_device_id:
            await self.crypto_store.put_device_id(self.device_id)

    async def _start(self, try_n: Optional[int] = 0) -> None:
        if not self.enabled:
            self.log.debug("Not starting disabled client")
            return
        elif self.started:
            self.log.warning("Ignoring start() call to started client")
            return
        try:
            whoami = await self.client.whoami()
        except MatrixInvalidToken as e:
            self.log.error(f"Invalid token: {e}. Disabling client")
            self.db_instance.enabled = False
            return
        except Exception as e:
            if try_n >= 8:
                self.log.exception("Failed to get /account/whoami, disabling client")
                self.db_instance.enabled = False
            else:
                self.log.warning(f"Failed to get /account/whoami, "
                                 f"retrying in {(try_n + 1) * 10}s: {e}")
                _ = asyncio.ensure_future(self.start(try_n + 1), loop=self.loop)
            return
        if whoami.user_id != self.id:
            self.log.error(f"User ID mismatch: expected {self.id}, but got {whoami.user_id}")
            self.db_instance.enabled = False
            return
        elif whoami.device_id and self.device_id and whoami.device_id != self.device_id:
            self.log.error(f"Device ID mismatch: expected {self.device_id}, "
                           f"but got {whoami.device_id}")
            self.db_instance.enabled = False
            return
        if not self.filter_id:
            self.db_instance.edit(filter_id=await self.client.create_filter(Filter(
                room=RoomFilter(
                    timeline=RoomEventFilter(
                        limit=50,
                        lazy_load_members=True,
                    ),
                    state=StateFilter(
                        lazy_load_members=True,
                    )
                ),
                presence=EventFilter(
                    not_types=[EventType.PRESENCE],
                ),
            )))
        if self.displayname != "disable":
            await self.client.set_displayname(self.displayname)
        if self.avatar_url != "disable":
            await self.client.set_avatar_url(self.avatar_url)
        if self.crypto:
            await self._start_crypto()
        self.start_sync()
        await self._update_remote_profile()
        self.started = True
        self.log.info("Client started, starting plugin instances...")
        await self.start_plugins()

    async def start_plugins(self) -> None:
        await asyncio.gather(*[plugin.start() for plugin in self.references])

    async def stop_plugins(self) -> None:
        await asyncio.gather(*[plugin.stop() for plugin in self.references if plugin.started])

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
            if self.crypto:
                await self.crypto_store.close()

    def clear_cache(self) -> None:
        self.stop_sync()
        self.db_instance.edit(filter_id="", next_batch="")
        self.start_sync()

    def delete(self) -> None:
        try:
            del self.cache[self.id]
        except KeyError:
            pass
        self.db_instance.delete()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "homeserver": self.homeserver,
            "access_token": self.access_token,
            "device_id": self.device_id,
            "fingerprint": (self.crypto.account.fingerprint if self.crypto and self.crypto.account
                            else None),
            "enabled": self.enabled,
            "started": self.started,
            "sync": self.sync,
            "sync_ok": self.sync_ok,
            "autojoin": self.autojoin,
            "online": self.online,
            "displayname": self.displayname,
            "avatar_url": self.avatar_url,
            "remote_displayname": self.remote_displayname,
            "remote_avatar_url": self.remote_avatar_url,
            "instances": [instance.to_dict() for instance in self.references],
        }

    @classmethod
    def get(cls, user_id: UserID, db_instance: Optional[DBClient] = None) -> Optional['Client']:
        try:
            return cls.cache[user_id]
        except KeyError:
            db_instance = db_instance or DBClient.get(user_id)
            if not db_instance:
                return None
            return Client(db_instance)

    @classmethod
    def all(cls) -> Iterable['Client']:
        return (cls.get(user.id, user) for user in DBClient.all())

    async def _handle_tombstone(self, evt: StateEvent) -> None:
        if not evt.content.replacement_room:
            self.log.info(f"{evt.room_id} tombstoned with no replacement, ignoring")
            return
        _, server = self.client.parse_user_id(evt.sender)
        await self.client.join_room(evt.content.replacement_room, servers=[server])

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
        if self.displayname != "disable":
            await self.client.set_displayname(self.displayname)
        else:
            await self._update_remote_profile()

    async def update_avatar_url(self, avatar_url: ContentURI) -> None:
        if avatar_url is None or avatar_url == self.avatar_url:
            return
        self.db_instance.avatar_url = avatar_url
        if self.avatar_url != "disable":
            await self.client.set_avatar_url(self.avatar_url)
        else:
            await self._update_remote_profile()

    async def update_access_details(self, access_token: Optional[str], homeserver: Optional[str],
                                    device_id: Optional[str] = None) -> None:
        if not access_token and not homeserver:
            return
        if device_id is None:
            device_id = self.device_id
        elif not device_id:
            device_id = None
        if (
            access_token == self.access_token
            and homeserver == self.homeserver
            and device_id == self.device_id
        ):
            return
        new_client = MaubotMatrixClient(mxid=self.id, base_url=homeserver or self.homeserver,
                                        token=access_token or self.access_token, loop=self.loop,
                                        device_id=device_id, client_session=self.http_client,
                                        log=self.log, state_store=self.global_state_store)
        whoami = await new_client.whoami()
        if whoami.user_id != self.id:
            raise ValueError(f"MXID mismatch: {whoami.user_id}")
        elif whoami.device_id and device_id and whoami.device_id != device_id:
            raise ValueError(f"Device ID mismatch: {whoami.device_id}")
        new_client.sync_store = SyncStoreProxy(self.db_instance)
        self.stop_sync()

        # TODO this event handler transfer is pretty hacky
        self._remove_crypto_event_handlers()
        self.client.crypto = None
        new_client.event_handlers = self.client.event_handlers
        new_client.global_event_handlers = self.client.global_event_handlers

        self.client = new_client
        self.db_instance.homeserver = homeserver
        self.db_instance.access_token = access_token
        self.db_instance.device_id = device_id
        if self.enable_crypto:
            self._prepare_crypto()
            await self._start_crypto()
        else:
            self.crypto_store = None
            self.crypto = None
        self.start_sync()

    async def _update_remote_profile(self) -> None:
        profile = await self.client.get_profile(self.id)
        self.remote_displayname, self.remote_avatar_url = profile.displayname, profile.avatar_url

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
    def device_id(self) -> DeviceID:
        return self.db_instance.device_id

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
            self.client.add_event_handler(EventType.ROOM_MEMBER, self._handle_invite)
        else:
            self.client.remove_event_handler(EventType.ROOM_MEMBER, self._handle_invite)
        self.db_instance.autojoin = value

    @property
    def online(self) -> bool:
        return self.db_instance.online

    @online.setter
    def online(self, value: bool) -> None:
        self.client.presence = PresenceState.ONLINE if value else PresenceState.OFFLINE
        self.db_instance.online = value

    @property
    def displayname(self) -> str:
        return self.db_instance.displayname

    @property
    def avatar_url(self) -> ContentURI:
        return self.db_instance.avatar_url

    # endregion


def init(config: 'Config', loop: asyncio.AbstractEventLoop) -> Iterable[Client]:
    Client.http_client = ClientSession(loop=loop)
    Client.loop = loop

    if OlmMachine:
        db_url = config["crypto_database"]
        if db_url == "default":
            db_url = config["database"]
        Client.crypto_db = AsyncDatabase.create(db_url, upgrade_table=PgCryptoStore.upgrade_table)

    return Client.all()

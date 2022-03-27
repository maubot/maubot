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

from typing import TYPE_CHECKING, Any, AsyncGenerator, AsyncIterable, Awaitable, Callable, cast
from collections import defaultdict
import asyncio
import logging

from aiohttp import ClientSession

from mautrix.client import InternalEventType
from mautrix.errors import MatrixInvalidToken
from mautrix.types import (
    ContentURI,
    DeviceID,
    EventFilter,
    EventType,
    Filter,
    FilterID,
    Membership,
    PresenceState,
    RoomEventFilter,
    RoomFilter,
    StateEvent,
    StateFilter,
    StrippedStateEvent,
    SyncToken,
    UserID,
)
from mautrix.util.async_getter_lock import async_getter_lock
from mautrix.util.logging import TraceLogger

from .db import Client as DBClient
from .matrix import MaubotMatrixClient

try:
    from mautrix.crypto import OlmMachine, PgCryptoStore

    crypto_import_error = None
except ImportError as e:
    OlmMachine = PgCryptoStore = None
    crypto_import_error = e

if TYPE_CHECKING:
    from .__main__ import Maubot
    from .instance import PluginInstance


class Client(DBClient):
    maubot: "Maubot" = None
    cache: dict[UserID, Client] = {}
    _async_get_locks: dict[Any, asyncio.Lock] = defaultdict(lambda: asyncio.Lock())
    log: TraceLogger = logging.getLogger("maubot.client")

    http_client: ClientSession = None

    references: set[PluginInstance]
    client: MaubotMatrixClient
    crypto: OlmMachine | None
    crypto_store: PgCryptoStore | None
    started: bool
    sync_ok: bool

    remote_displayname: str | None
    remote_avatar_url: ContentURI | None

    def __init__(
        self,
        id: UserID,
        homeserver: str,
        access_token: str,
        device_id: DeviceID,
        enabled: bool = False,
        next_batch: SyncToken = "",
        filter_id: FilterID = "",
        sync: bool = True,
        autojoin: bool = True,
        online: bool = True,
        displayname: str = "disable",
        avatar_url: str = "disable",
    ) -> None:
        super().__init__(
            id=id,
            homeserver=homeserver,
            access_token=access_token,
            device_id=device_id,
            enabled=bool(enabled),
            next_batch=next_batch,
            filter_id=filter_id,
            sync=bool(sync),
            autojoin=bool(autojoin),
            online=bool(online),
            displayname=displayname,
            avatar_url=avatar_url,
        )
        self._postinited = False

    def __hash__(self) -> int:
        return hash(self.id)

    @classmethod
    def init_cls(cls, maubot: "Maubot") -> None:
        cls.maubot = maubot

    def _make_client(
        self, homeserver: str | None = None, token: str | None = None, device_id: str | None = None
    ) -> MaubotMatrixClient:
        return MaubotMatrixClient(
            mxid=self.id,
            base_url=homeserver or self.homeserver,
            token=token or self.access_token,
            client_session=self.http_client,
            log=self.log,
            crypto_log=self.log.getChild("crypto"),
            loop=self.maubot.loop,
            device_id=device_id or self.device_id,
            sync_store=self,
            state_store=self.maubot.state_store,
        )

    def postinit(self) -> None:
        if self._postinited:
            raise RuntimeError("postinit() called twice")
        self._postinited = True
        self.cache[self.id] = self
        self.log = self.log.getChild(self.id)
        self.http_client = ClientSession(loop=self.maubot.loop)
        self.references = set()
        self.started = False
        self.sync_ok = True
        self.remote_displayname = None
        self.remote_avatar_url = None
        self.client = self._make_client()
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

    def _set_sync_ok(self, ok: bool) -> Callable[[dict[str, Any]], Awaitable[None]]:
        async def handler(data: dict[str, Any]) -> None:
            self.sync_ok = ok

        return handler

    @property
    def enable_crypto(self) -> bool:
        if not self.device_id:
            return False
        elif not OlmMachine:
            global crypto_import_error
            self.log.warning(
                "Client has device ID, but encryption dependencies not installed",
                exc_info=crypto_import_error,
            )
            # Clear the stack trace after it's logged once to avoid spamming logs
            crypto_import_error = None
            return False
        elif not self.maubot.crypto_db:
            self.log.warning("Client has device ID, but crypto database is not prepared")
            return False
        return True

    def _prepare_crypto(self) -> None:
        self.crypto_store = PgCryptoStore(
            account_id=self.id, pickle_key="mau.crypto", db=self.maubot.crypto_db
        )
        self.crypto = OlmMachine(
            self.client,
            self.crypto_store,
            self.maubot.state_store,
            log=self.client.crypto_log,
        )
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

    async def start(self, try_n: int | None = 0) -> None:
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
            self.log.warning(
                "Mismatching device ID in crypto store and main database, resetting encryption"
            )
            await self.crypto_store.delete()
            crypto_device_id = None
        await self.crypto.load()
        if not crypto_device_id:
            await self.crypto_store.put_device_id(self.device_id)

    async def _start(self, try_n: int | None = 0) -> None:
        if not self.enabled:
            self.log.debug("Not starting disabled client")
            return
        elif self.started:
            self.log.warning("Ignoring start() call to started client")
            return
        try:
            await self.client.versions()
            whoami = await self.client.whoami()
        except MatrixInvalidToken as e:
            self.log.error(f"Invalid token: {e}. Disabling client")
            self.enabled = False
            await self.update()
            return
        except Exception as e:
            if try_n >= 8:
                self.log.exception("Failed to get /account/whoami, disabling client")
                self.enabled = False
                await self.update()
            else:
                self.log.warning(
                    f"Failed to get /account/whoami, retrying in {(try_n + 1) * 10}s: {e}"
                )
                _ = asyncio.create_task(self.start(try_n + 1))
            return
        if whoami.user_id != self.id:
            self.log.error(f"User ID mismatch: expected {self.id}, but got {whoami.user_id}")
            self.enabled = False
            await self.update()
            return
        elif whoami.device_id and self.device_id and whoami.device_id != self.device_id:
            self.log.error(
                f"Device ID mismatch: expected {self.device_id}, but got {whoami.device_id}"
            )
            self.enabled = False
            await self.update()
            return
        if not self.filter_id:
            self.filter_id = await self.client.create_filter(
                Filter(
                    room=RoomFilter(
                        timeline=RoomEventFilter(
                            limit=50,
                            lazy_load_members=True,
                        ),
                        state=StateFilter(
                            lazy_load_members=True,
                        ),
                    ),
                    presence=EventFilter(
                        not_types=[EventType.PRESENCE],
                    ),
                )
            )
            await self.update()
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

    async def clear_cache(self) -> None:
        self.stop_sync()
        self.filter_id = FilterID("")
        self.next_batch = SyncToken("")
        await self.update()
        self.start_sync()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "homeserver": self.homeserver,
            "access_token": self.access_token,
            "device_id": self.device_id,
            "fingerprint": (
                self.crypto.account.fingerprint if self.crypto and self.crypto.account else None
            ),
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

    async def _handle_tombstone(self, evt: StateEvent) -> None:
        if not evt.content.replacement_room:
            self.log.info(f"{evt.room_id} tombstoned with no replacement, ignoring")
            return
        _, server = self.client.parse_user_id(evt.sender)
        await self.client.join_room(evt.content.replacement_room, servers=[server])

    async def _handle_invite(self, evt: StrippedStateEvent) -> None:
        if evt.state_key == self.id and evt.content.membership == Membership.INVITE:
            await self.client.join_room(evt.room_id)

    async def update_started(self, started: bool | None) -> None:
        if started is None or started == self.started:
            return
        if started:
            await self.start()
        else:
            await self.stop()

    async def update_enabled(self, enabled: bool | None, save: bool = True) -> None:
        if enabled is None or enabled == self.enabled:
            return
        self.enabled = enabled
        if save:
            await self.update()

    async def update_displayname(self, displayname: str | None, save: bool = True) -> None:
        if displayname is None or displayname == self.displayname:
            return
        self.displayname = displayname
        if self.displayname != "disable":
            await self.client.set_displayname(self.displayname)
        else:
            await self._update_remote_profile()
        if save:
            await self.update()

    async def update_avatar_url(self, avatar_url: ContentURI, save: bool = True) -> None:
        if avatar_url is None or avatar_url == self.avatar_url:
            return
        self.avatar_url = avatar_url
        if self.avatar_url != "disable":
            await self.client.set_avatar_url(self.avatar_url)
        else:
            await self._update_remote_profile()
        if save:
            await self.update()

    async def update_sync(self, sync: bool | None, save: bool = True) -> None:
        if sync is None or self.sync == sync:
            return
        self.sync = sync
        if self.started:
            if sync:
                self.start_sync()
            else:
                self.stop_sync()
        if save:
            await self.update()

    async def update_autojoin(self, autojoin: bool | None, save: bool = True) -> None:
        if autojoin is None or autojoin == self.autojoin:
            return
        if autojoin:
            self.client.add_event_handler(EventType.ROOM_MEMBER, self._handle_invite)
        else:
            self.client.remove_event_handler(EventType.ROOM_MEMBER, self._handle_invite)
        self.autojoin = autojoin
        if save:
            await self.update()

    async def update_online(self, online: bool | None, save: bool = True) -> None:
        if online is None or online == self.online:
            return
        self.client.presence = PresenceState.ONLINE if online else PresenceState.OFFLINE
        self.online = online
        if save:
            await self.update()

    async def update_access_details(
        self,
        access_token: str | None,
        homeserver: str | None,
        device_id: str | None = None,
    ) -> None:
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
        new_client = self._make_client(homeserver, access_token, device_id)
        whoami = await new_client.whoami()
        if whoami.user_id != self.id:
            raise ValueError(f"MXID mismatch: {whoami.user_id}")
        elif whoami.device_id and device_id and whoami.device_id != device_id:
            raise ValueError(f"Device ID mismatch: {whoami.device_id}")
        new_client.sync_store = self
        self.stop_sync()

        # TODO this event handler transfer is pretty hacky
        self._remove_crypto_event_handlers()
        self.client.crypto = None
        new_client.event_handlers = self.client.event_handlers
        new_client.global_event_handlers = self.client.global_event_handlers

        self.client = new_client
        self.homeserver = homeserver
        self.access_token = access_token
        self.device_id = device_id
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

    async def delete(self) -> None:
        try:
            del self.cache[self.id]
        except KeyError:
            pass
        await super().delete()

    @classmethod
    @async_getter_lock
    async def get(
        cls,
        user_id: UserID,
        *,
        homeserver: str | None = None,
        access_token: str | None = None,
        device_id: DeviceID | None = None,
    ) -> Client | None:
        try:
            return cls.cache[user_id]
        except KeyError:
            pass

        user = cast(cls, await super().get(user_id))
        if user is not None:
            user.postinit()
            return user

        if homeserver and access_token:
            user = cls(
                user_id,
                homeserver=homeserver,
                access_token=access_token,
                device_id=device_id or "",
            )
            await user.insert()
            user.postinit()
            return user

        return None

    @classmethod
    async def all(cls) -> AsyncGenerator[Client, None]:
        users = await super().all()
        user: cls
        for user in users:
            try:
                yield cls.cache[user.id]
            except KeyError:
                user.postinit()
                yield user

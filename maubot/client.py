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
from typing import Dict, Optional
from aiohttp import ClientSession
import logging

from mautrix import ClientAPI
from mautrix.types import UserID, SyncToken, FilterID, ContentURI

from .db import DBClient

log = logging.getLogger("maubot.client")


class Client:
    cache: Dict[UserID, 'Client'] = {}
    http_client: ClientSession = None

    def __init__(self, db_instance: DBClient) -> None:
        self.db_instance: DBClient = db_instance
        self.cache[self.id] = self
        self.client: ClientAPI = ClientAPI(mxid=self.id,
                                           base_url=self.homeserver,
                                           token=self.access_token,
                                           client_session=self.http_client,
                                           log=log.getChild(self.id))

    @classmethod
    def get(cls, id: UserID) -> Optional['Client']:
        try:
            return cls.cache[id]
        except KeyError:
            db_instance = DBClient.query.get(id)
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

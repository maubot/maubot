# maubot - A plugin-based Matrix bot system.
# Copyright (C) 2019 Tulir Asokan
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
from typing import Iterable, Optional
import logging
import sys

from sqlalchemy import Column, String, Boolean, ForeignKey, Text
from sqlalchemy.engine.base import Engine
import sqlalchemy as sql

from mautrix.types import UserID, FilterID, DeviceID, SyncToken, ContentURI
from mautrix.util.db import Base
from mautrix.client.state_store.sqlalchemy import RoomState, UserProfile

from .config import Config


class DBPlugin(Base):
    __tablename__ = "plugin"

    id: str = Column(String(255), primary_key=True)
    type: str = Column(String(255), nullable=False)
    enabled: bool = Column(Boolean, nullable=False, default=False)
    primary_user: UserID = Column(String(255),
                                  ForeignKey("client.id", onupdate="CASCADE", ondelete="RESTRICT"),
                                  nullable=False)
    config: str = Column(Text, nullable=False, default='')

    @classmethod
    def all(cls) -> Iterable['DBPlugin']:
        return cls._select_all()

    @classmethod
    def get(cls, id: str) -> Optional['DBPlugin']:
        return cls._select_one_or_none(cls.c.id == id)


class DBClient(Base):
    __tablename__ = "client"

    id: UserID = Column(String(255), primary_key=True)
    homeserver: str = Column(String(255), nullable=False)
    access_token: str = Column(Text, nullable=False)
    device_id: DeviceID = Column(String(255), nullable=True)
    enabled: bool = Column(Boolean, nullable=False, default=False)

    next_batch: SyncToken = Column(String(255), nullable=False, default="")
    filter_id: FilterID = Column(String(255), nullable=False, default="")

    sync: bool = Column(Boolean, nullable=False, default=True)
    autojoin: bool = Column(Boolean, nullable=False, default=True)
    online: bool = Column(Boolean, nullable=False, default=True)

    displayname: str = Column(String(255), nullable=False, default="")
    avatar_url: ContentURI = Column(String(255), nullable=False, default="")

    @classmethod
    def all(cls) -> Iterable['DBClient']:
        return cls._select_all()

    @classmethod
    def get(cls, id: str) -> Optional['DBClient']:
        return cls._select_one_or_none(cls.c.id == id)


def init(config: Config) -> Engine:
    db = sql.create_engine(config["database"])
    Base.metadata.bind = db

    for table in (DBPlugin, DBClient, RoomState, UserProfile):
        table.bind(db)

    if not db.has_table("alembic_version"):
        log = logging.getLogger("maubot.db")

        if db.has_table("client") and db.has_table("plugin"):
            log.warning("alembic_version table not found, but client and plugin tables found. "
                        "Assuming pre-Alembic database and inserting version.")
            db.execute("CREATE TABLE IF NOT EXISTS alembic_version ("
                       "    version_num VARCHAR(32) PRIMARY KEY"
                       ");")
            db.execute("INSERT INTO alembic_version VALUES ('d295f8dcfa64');")
        else:
            log.critical("alembic_version table not found. "
                         "Did you forget to `alembic upgrade head`?")
            sys.exit(10)

    return db

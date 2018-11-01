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
from typing import cast

from sqlalchemy import Column, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import Query, Session, sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy as sql

from mautrix.types import UserID, FilterID, SyncToken, ContentURI

from .config import Config

Base: declarative_base = declarative_base()


class DBPlugin(Base):
    query: Query
    __tablename__ = "plugin"

    id: str = Column(String(255), primary_key=True)
    type: str = Column(String(255), nullable=False)
    enabled: bool = Column(Boolean, nullable=False, default=False)
    primary_user: UserID = Column(String(255),
                                  ForeignKey("client.id", onupdate="CASCADE", ondelete="RESTRICT"),
                                  nullable=False)
    config: str = Column(Text, nullable=False, default='')


class DBClient(Base):
    query: Query
    __tablename__ = "client"

    id: UserID = Column(String(255), primary_key=True)
    homeserver: str = Column(String(255), nullable=False)
    access_token: str = Column(String(255), nullable=False)
    enabled: bool = Column(Boolean, nullable=False, default=False)

    next_batch: SyncToken = Column(String(255), nullable=False, default="")
    filter_id: FilterID = Column(String(255), nullable=False, default="")

    sync: bool = Column(Boolean, nullable=False, default=True)
    autojoin: bool = Column(Boolean, nullable=False, default=True)

    displayname: str = Column(String(255), nullable=False, default="")
    avatar_url: ContentURI = Column(String(255), nullable=False, default="")


def init(config: Config) -> Session:
    db_engine: sql.engine.Engine = sql.create_engine(config["database"])
    db_factory = sessionmaker(bind=db_engine)
    db_session = scoped_session(db_factory)
    Base.metadata.bind = db_engine
    Base.metadata.create_all()

    DBPlugin.query = db_session.query_property()
    DBClient.query = db_session.query_property()

    return cast(Session, db_session)

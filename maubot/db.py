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
from sqlalchemy import (Column, String, Boolean, ForeignKey, Text, TypeDecorator)
from sqlalchemy.orm import Query
from sqlalchemy.ext.declarative import declarative_base
import json

from mautrix.types import JSON, UserID, FilterID, SyncToken, ContentURI

Base: declarative_base = declarative_base()


class JSONEncodedDict(TypeDecorator):
    impl = Text

    @property
    def python_type(self):
        return dict

    def process_literal_param(self, value, _):
        return json.dumps(value) if value is not None else None

    def process_bind_param(self, value, _):
        return json.dumps(value) if value is not None else None

    def process_result_value(self, value, _):
        return json.loads(value) if value is not None else None


class DBPlugin(Base):
    query: Query
    __tablename__ = "plugin"

    id: str = Column(String(255), primary_key=True)
    type: str = Column(String(255), nullable=False)
    enabled: bool = Column(Boolean, nullable=False, default=False)
    primary_user: UserID = Column(String(255),
                                  ForeignKey("client.id", onupdate="CASCADE", ondelete="RESTRICT"),
                                  nullable=False)


class DBClient(Base):
    query: Query
    __tablename__ = "client"

    id: UserID = Column(String(255), primary_key=True)
    homeserver: str = Column(String(255), nullable=False)
    access_token: str = Column(String(255), nullable=False)

    next_batch: SyncToken = Column(String(255), nullable=False, default="")
    filter_id: FilterID = Column(String(255), nullable=False, default="")

    sync: bool = Column(Boolean, nullable=False, default=True)
    autojoin: bool = Column(Boolean, nullable=False, default=True)

    displayname: str = Column(String(255), nullable=False, default="")
    avatar_url: ContentURI = Column(String(255), nullable=False, default="")


class DBCommandSpec(Base):
    query: Query
    __tablename__ = "command_spec"

    owner: str = Column(String(255),
                        ForeignKey("plugin.id", onupdate="CASCADE", ondelete="CASCADE"),
                        primary_key=True)
    client: UserID = Column(String(255),
                            ForeignKey("client.id", onupdate="CASCADE", ondelete="CASCADE"),
                            primary_key=True)
    spec: JSON = Column(JSONEncodedDict, nullable=False)

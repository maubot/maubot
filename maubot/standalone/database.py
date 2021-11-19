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
from typing import Optional

import sqlalchemy as sql

from mautrix.util.db import Base
from mautrix.types import UserID, SyncToken, FilterID


class NextBatch(Base):
    __tablename__ = "standalone_next_batch"

    user_id: UserID = sql.Column(sql.String(255), primary_key=True)
    next_batch: SyncToken = sql.Column(sql.String(255))
    filter_id: FilterID = sql.Column(sql.String(255))

    @classmethod
    def get(cls, user_id: UserID) -> Optional['NextBatch']:
        return cls._select_one_or_none(cls.c.user_id == user_id)

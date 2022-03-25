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

from attr import dataclass

from mautrix.client import SyncStore
from mautrix.types import FilterID, SyncToken, UserID
from mautrix.util.async_db import Database

find_q = "SELECT next_batch, filter_id FROM standalone_next_batch WHERE user_id=$1"
insert_q = "INSERT INTO standalone_next_batch (user_id, next_batch, filter_id) VALUES ($1, $2, $3)"
update_nb_q = "UPDATE standalone_next_batch SET next_batch=$1 WHERE user_id=$2"
update_filter_q = "UPDATE standalone_next_batch SET filter_id=$1 WHERE user_id=$2"


@dataclass
class NextBatch(SyncStore):
    db: Database
    user_id: UserID
    next_batch: SyncToken = ""
    filter_id: FilterID = ""

    async def load(self) -> NextBatch:
        row = await self.db.fetchrow(find_q, self.user_id)
        if row is not None:
            self.next_batch = row["next_batch"]
            self.filter_id = row["filter_id"]
        else:
            await self.db.execute(insert_q, self.user_id, self.next_batch, self.filter_id)
        return self

    async def put_filter_id(self, filter_id: FilterID) -> None:
        self.filter_id = filter_id
        await self.db.execute(update_filter_q, self.filter_id, self.user_id)

    async def put_next_batch(self, next_batch: SyncToken) -> None:
        self.next_batch = next_batch
        await self.db.execute(update_nb_q, self.next_batch, self.user_id)

    async def get_next_batch(self) -> SyncToken:
        return self.next_batch

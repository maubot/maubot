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
from mautrix.client import ClientStore
from mautrix.types import SyncToken


class ClientStoreProxy(ClientStore):
    def __init__(self, db_instance) -> None:
        self.db_instance = db_instance

    @property
    def next_batch(self) -> SyncToken:
        return self.db_instance.next_batch

    @next_batch.setter
    def next_batch(self, value: SyncToken) -> None:
        self.db_instance.edit(next_batch=value)

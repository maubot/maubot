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
from mautrix.client.state_store.asyncpg import PgStateStore as BasePgStateStore

try:
    from mautrix.crypto import StateStore as CryptoStateStore

    class PgStateStore(BasePgStateStore, CryptoStateStore):
        pass

except ImportError as e:
    PgStateStore = BasePgStateStore

__all__ = ["PgStateStore"]

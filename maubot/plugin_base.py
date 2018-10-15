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
from typing import TYPE_CHECKING
from abc import ABC

if TYPE_CHECKING:
    from .client import MaubotMatrixClient
    from .command_spec import CommandSpec


class Plugin(ABC):
    def __init__(self, client: 'MaubotMatrixClient') -> None:
        self.client = client

    def set_command_spec(self, spec: 'CommandSpec') -> None:
        pass

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

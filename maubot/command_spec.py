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
from typing import List, Dict
from attr import dataclass

from mautrix.types import Event
from mautrix.client.api.types.util import SerializableAttrs


@dataclass
class Argument(SerializableAttrs['Argument']):
    matches: str
    required: bool = False
    description: str = None


@dataclass
class Command(SerializableAttrs['Command']):
    syntax: str
    arguments: Dict[str, Argument]
    description: str = None


@dataclass
class PassiveCommand(SerializableAttrs['PassiveCommand']):
    name: str
    matches: str
    match_against: str
    match_event: Event = None


@dataclass
class CommandSpec(SerializableAttrs['CommandSpec']):
    commands: List[Command] = []
    passive_commands: List[PassiveCommand] = []

    def __add__(self, other: 'CommandSpec') -> 'CommandSpec':
        return CommandSpec(commands=self.commands + other.commands,
                           passive_commands=self.passive_commands + other.passive_commands)

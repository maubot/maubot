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
from typing import List, Dict, Pattern, Union, Tuple, Optional, Any
from attr import dataclass
import re

from mautrix.types import MessageEvent, MatchedCommand, MatchedPassiveCommand
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
    match_event: MessageEvent = None


class ParsedCommand:
    name: str
    is_passive: bool
    arguments: List[str]
    starts_with: str
    matches: Pattern
    match_against: str
    match_event: MessageEvent

    def __init__(self, command: Union[PassiveCommand, Command]) -> None:
        if isinstance(command, PassiveCommand):
            self._init_passive(command)
        elif isinstance(command, Command):
            self._init_active(command)
        else:
            raise ValueError("Command parameter must be a Command or a PassiveCommand.")

    def _init_passive(self, command: PassiveCommand) -> None:
        self.name = command.name
        self.is_passive = True
        self.match_against = command.match_against
        self.matches = re.compile(command.matches)
        self.match_event = command.match_event

    def _init_active(self, command: Command) -> None:
        self.name = command.syntax
        self.is_passive = False
        self.arguments = []

        regex_builder = []
        sw_builder = []
        argument_encountered = False

        for word in command.syntax.split(" "):
            arg = command.arguments.get(word, None)
            if arg is not None and len(word) > 0:
                argument_encountered = True
                regex = f"({arg.matches})" if arg.required else f"(?:{arg.matches})?"
                self.arguments.append(word)
                regex_builder.append(regex)
            else:
                if not argument_encountered:
                    sw_builder.append(word)
                regex_builder.append(re.escape(word))
        self.starts_with = "!" + " ".join(sw_builder)
        self.matches = re.compile("^!" + " ".join(regex_builder) + "$")
        self.match_against = "body"

    def match(self, evt: MessageEvent) -> bool:
        return self._match_passive(evt) if self.is_passive else self._match_active(evt)

    @staticmethod
    def _parse_key(key: str) -> Tuple[str, Optional[str]]:
        if '.' not in key:
            return key, None
        key, next_key = key.split('.', 1)
        if len(key) > 0 and key[0] == "[":
            end_index = next_key.index("]")
            key = key[1:] + "." + next_key[:end_index]
            next_key = next_key[end_index + 2:] if len(next_key) > end_index + 1 else None
        return key, next_key

    @classmethod
    def _recursive_get(cls, data: Any, key: str) -> Any:
        if not data:
            return None
        key, next_key = cls._parse_key(key)
        if next_key is not None:
            return cls._recursive_get(data[key], next_key)
        return data[key]

    def _match_passive(self, evt: MessageEvent) -> bool:
        try:
            match_against = self._recursive_get(evt.content, self.match_against)
        except KeyError:
            match_against = None
        match_against = match_against or evt.content.body
        matches = [[match.string[match.start():match.end()]] + list(match.groups())
                   for match in self.matches.finditer(match_against)]
        if not matches:
            return False
        if evt.unsigned.passive_command is None:
            evt.unsigned.passive_command = {}
        evt.unsigned.passive_command[self.name] = MatchedPassiveCommand(captured=matches)
        return True

    def _match_active(self, evt: MessageEvent) -> bool:
        if not evt.content.body.startswith(self.starts_with):
            return False
        match = self.matches.match(evt.content.body)
        if not match:
            return False
        evt.content.command = MatchedCommand(matched=self.name,
                                             arguments=dict(zip(self.arguments, match.groups())))
        return True


@dataclass
class CommandSpec(SerializableAttrs['CommandSpec']):
    commands: List[Command] = []
    passive_commands: List[PassiveCommand] = []

    def __add__(self, other: 'CommandSpec') -> 'CommandSpec':
        return CommandSpec(commands=self.commands + other.commands,
                           passive_commands=self.passive_commands + other.passive_commands)

    def parse(self) -> List[ParsedCommand]:
        return [ParsedCommand(command) for command in self.commands + self.passive_commands]

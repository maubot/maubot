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
from typing import Dict, List, Union, Callable

from mautrix import Client as MatrixClient
from mautrix.client import EventHandler
from mautrix.types import EventType, MessageEvent

from .command_spec import ParsedCommand, CommandSpec


class MaubotMatrixClient(MatrixClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.command_handlers: Dict[str, List[EventHandler]] = {}
        self.commands: List[ParsedCommand] = []
        self.command_specs: Dict[str, CommandSpec] = {}

        self.add_event_handler(self._command_event_handler, EventType.ROOM_MESSAGE)

    def set_command_spec(self, plugin_id: str, spec: CommandSpec) -> None:
        self.command_specs[plugin_id] = spec
        self._reparse_command_specs()

    def _reparse_command_specs(self) -> None:
        self.commands = [parsed_command
                         for spec in self.command_specs.values()
                         for parsed_command in spec.parse()]

    def remove_command_spec(self, plugin_id: str) -> None:
        try:
            del self.command_specs[plugin_id]
            self._reparse_command_specs()
        except KeyError:
            pass

    async def _command_event_handler(self, evt: MessageEvent) -> None:
        for command in self.commands:
            if command.match(evt):
                await self._trigger_command(command, evt)
                return

    async def _trigger_command(self, command: ParsedCommand, evt: MessageEvent) -> None:
        for handler in self.command_handlers.get(command.name, []):
            await handler(evt)

    def on(self, var: Union[EventHandler, EventType, str]
           ) -> Union[EventHandler, Callable[[EventHandler], EventHandler]]:
        if isinstance(var, str):
            def decorator(func: EventHandler) -> EventHandler:
                self.add_command_handler(var, func)
                return func

            return decorator
        return super().on(var)

    def add_command_handler(self, command: str, handler: EventHandler) -> None:
        self.command_handlers.setdefault(command, []).append(handler)

    def remove_command_handler(self, command: str, handler: EventHandler) -> None:
        try:
            self.command_handlers[command].remove(handler)
        except (KeyError, ValueError):
            pass

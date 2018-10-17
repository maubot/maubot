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
from typing import Dict, List, Union, Callable, Awaitable
import attr
import commonmark

from mautrix import Client as MatrixClient
from mautrix.client import EventHandler
from mautrix.types import (EventType, MessageEvent, Event, EventID, RoomID, MessageEventContent,
                           MessageType, TextMessageEventContent, Format)

from .command_spec import ParsedCommand, CommandSpec


class MaubotMessageEvent(MessageEvent):
    _client: MatrixClient

    def __init__(self, base: MessageEvent, client: MatrixClient):
        super().__init__(**{a.name.lstrip("_"): getattr(base, a.name)
                            for a in attr.fields(MessageEvent)})
        self._client = client

    def respond(self, content: Union[str, MessageEventContent],
                event_type: EventType = EventType.ROOM_MESSAGE,
                markdown: bool = True) -> Awaitable[EventID]:
        if isinstance(content, str):
            content = TextMessageEventContent(msgtype=MessageType.NOTICE, body=content)
            if markdown:
                content.format = Format.HTML
                content.formatted_body = commonmark.commonmark(content.body)
        return self._client.send_message_event(self.room_id, event_type, content)

    def reply(self, content: Union[str, MessageEventContent],
              event_type: EventType = EventType.ROOM_MESSAGE,
              markdown: bool = True) -> Awaitable[EventID]:
        if isinstance(content, str):
            content = TextMessageEventContent(msgtype=MessageType.NOTICE, body=content)
            if markdown:
                content.format = Format.HTML
                content.formatted_body = commonmark.commonmark(content.body)
        content.set_reply(self)
        return self._client.send_message_event(self.room_id, event_type, content)

    def mark_read(self) -> Awaitable[None]:
        return self._client.send_receipt(self.room_id, self.event_id, "m.read")


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
        if evt.sender == self.mxid or evt.content.msgtype != MessageType.TEXT:
            return
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

    async def call_handlers(self, event: Event) -> None:
        if isinstance(event, MessageEvent):
            event = MaubotMessageEvent(event, self)
        return await super().call_handlers(event)

    async def get_event(self, room_id: RoomID, event_id: EventID) -> Event:
        event = await super().get_event(room_id, event_id)
        if isinstance(event, MessageEvent):
            return MaubotMessageEvent(event, self)
        return event

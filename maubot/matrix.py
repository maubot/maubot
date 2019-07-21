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
from typing import Union, Awaitable, Optional, Tuple
from markdown.extensions import Extension
import markdown as md
import attr

from mautrix.client import Client as MatrixClient, SyncStream
from mautrix.util.formatter import parse_html
from mautrix.types import (EventType, MessageEvent, Event, EventID, RoomID, MessageEventContent,
                           MessageType, TextMessageEventContent, Format, RelatesTo)


class EscapeHTML(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.deregister("html_block")
        md.inlinePatterns.deregister("html")


escape_html = EscapeHTML()


def parse_markdown(markdown: str, allow_html: bool = False) -> Tuple[str, str]:
    html = md.markdown(markdown, extensions=[escape_html] if not allow_html else [])
    return parse_html(html), html


class MaubotMessageEvent(MessageEvent):
    client: MatrixClient
    disable_reply: bool

    def __init__(self, base: MessageEvent, client: MatrixClient):
        super().__init__(**{a.name.lstrip("_"): getattr(base, a.name)
                            for a in attr.fields(MessageEvent)})
        self.client = client
        self.disable_reply = False

    def respond(self, content: Union[str, MessageEventContent],
                event_type: EventType = EventType.ROOM_MESSAGE, markdown: bool = True,
                html_in_markdown: bool = False, reply: bool = False) -> Awaitable[EventID]:
        if isinstance(content, str):
            content = TextMessageEventContent(msgtype=MessageType.NOTICE, body=content)
            if markdown:
                content.format = Format.HTML
                content.body, content.formatted_body = parse_markdown(content.body,
                                                                      allow_html=html_in_markdown)
        if reply and not self.disable_reply:
            content.set_reply(self)
        return self.client.send_message_event(self.room_id, event_type, content)

    def reply(self, content: Union[str, MessageEventContent],
              event_type: EventType = EventType.ROOM_MESSAGE, markdown: bool = True,
              html_in_markdown: bool = False) -> Awaitable[EventID]:
        return self.respond(content, event_type, markdown, reply=True,
                            html_in_markdown=html_in_markdown)

    def mark_read(self) -> Awaitable[None]:
        return self.client.send_receipt(self.room_id, self.event_id, "m.read")

    def react(self, key: str) -> Awaitable[None]:
        return self.client.react(self.room_id, self.event_id, key)


class MaubotMatrixClient(MatrixClient):
    def send_markdown(self, room_id: RoomID, markdown: str, msgtype: MessageType = MessageType.TEXT,
                      relates_to: Optional[RelatesTo] = None, **kwargs) -> Awaitable[EventID]:
        content = TextMessageEventContent(msgtype=msgtype, format=Format.HTML)
        content.body, content.formatted_body = parse_markdown(markdown)
        if relates_to:
            content.relates_to = relates_to
        return self.send_message(room_id, content, **kwargs)

    async def dispatch_event(self, event: Event, source: SyncStream = SyncStream.INTERNAL) -> None:
        if isinstance(event, MessageEvent):
            event = MaubotMessageEvent(event, self)
        elif source != SyncStream.INTERNAL:
            event.client = self
        return await super().dispatch_event(event, source)

    async def get_event(self, room_id: RoomID, event_id: EventID) -> Event:
        event = await super().get_event(room_id, event_id)
        if isinstance(event, MessageEvent):
            event.content.trim_reply_fallback()
            return MaubotMessageEvent(event, self)
        else:
            event.client = self
        return event

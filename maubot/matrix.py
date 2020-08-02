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
from typing import Union, Awaitable, Optional, Tuple, List
from html import escape
import asyncio

import attr

from mautrix.client import Client as MatrixClient, SyncStream
from mautrix.util.formatter import MatrixParser, MarkdownString, EntityType
from mautrix.util import markdown
from mautrix.types import (EventType, MessageEvent, Event, EventID, RoomID, MessageEventContent,
                           MessageType, TextMessageEventContent, Format, RelatesTo)


class HumanReadableString(MarkdownString):
    def format(self, entity_type: EntityType, **kwargs) -> 'MarkdownString':
        if entity_type == EntityType.URL and kwargs['url'] != self.text:
            self.text = f"{self.text} ({kwargs['url']})"
            return self
        return super(HumanReadableString, self).format(entity_type, **kwargs)


class MaubotHTMLParser(MatrixParser[HumanReadableString]):
    fs = HumanReadableString


def parse_formatted(message: str, allow_html: bool = False, render_markdown: bool = True
                    ) -> Tuple[str, str]:
    if render_markdown:
        html = markdown.render(message, allow_html=allow_html)
    elif allow_html:
        html = message
    else:
        return message, escape(message)
    return MaubotHTMLParser.parse(html).text, html


class MaubotMessageEvent(MessageEvent):
    client: 'MaubotMatrixClient'
    disable_reply: bool

    def __init__(self, base: MessageEvent, client: 'MaubotMatrixClient'):
        super().__init__(**{a.name.lstrip("_"): getattr(base, a.name)
                            for a in attr.fields(MessageEvent)})
        self.client = client
        self.disable_reply = client.disable_replies

    def respond(self, content: Union[str, MessageEventContent],
                event_type: EventType = EventType.ROOM_MESSAGE, markdown: bool = True,
                allow_html: bool = False, reply: Union[bool, str] = False,
                edits: Optional[Union[EventID, MessageEvent]] = None) -> Awaitable[EventID]:
        if isinstance(content, str):
            content = TextMessageEventContent(msgtype=MessageType.NOTICE, body=content)
            if allow_html or markdown:
                content.format = Format.HTML
                content.body, content.formatted_body = parse_formatted(content.body,
                                                                       render_markdown=markdown,
                                                                       allow_html=allow_html)
        if edits:
            content.set_edit(edits)
        elif reply:
            if reply != "force" and self.disable_reply:
                content.body = f"{self.sender}: {content.body}"
                fmt_body = content.formatted_body or escape(content.body).replace("\n", "<br>")
                content.formatted_body = (f'<a href="https://matrix.to/#/{self.sender}">'
                                          f'{self.sender}'
                                          f'</a>: {fmt_body}')
            else:
                content.set_reply(self)
        return self.client.send_message_event(self.room_id, event_type, content)

    def reply(self, content: Union[str, MessageEventContent],
              event_type: EventType = EventType.ROOM_MESSAGE, markdown: bool = True,
              allow_html: bool = False) -> Awaitable[EventID]:
        return self.respond(content, event_type, markdown=markdown, reply=True,
                            allow_html=allow_html)

    def mark_read(self) -> Awaitable[None]:
        return self.client.send_receipt(self.room_id, self.event_id, "m.read")

    def react(self, key: str) -> Awaitable[EventID]:
        return self.client.react(self.room_id, self.event_id, key)

    def edit(self, content: Union[str, MessageEventContent],
             event_type: EventType = EventType.ROOM_MESSAGE, markdown: bool = True,
             allow_html: bool = False) -> Awaitable[EventID]:
        return self.respond(content, event_type, markdown=markdown, edits=self,
                            allow_html=allow_html)


class MaubotMatrixClient(MatrixClient):
    disable_replies: bool

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.disable_replies = False

    def send_markdown(self, room_id: RoomID, markdown: str, *, allow_html: bool = False,
                      msgtype: MessageType = MessageType.TEXT,
                      edits: Optional[Union[EventID, MessageEvent]] = None,
                      relates_to: Optional[RelatesTo] = None, **kwargs
                      ) -> Awaitable[EventID]:
        content = TextMessageEventContent(msgtype=msgtype, format=Format.HTML)
        content.body, content.formatted_body = parse_formatted(markdown, allow_html=allow_html)
        if relates_to:
            if edits:
                raise ValueError("Can't use edits and relates_to at the same time.")
            content.relates_to = relates_to
        elif edits:
            content.set_edit(edits)
        return self.send_message(room_id, content, **kwargs)

    def dispatch_event(self, event: Event, source: SyncStream) -> List[asyncio.Task]:
        if isinstance(event, MessageEvent):
            event = MaubotMessageEvent(event, self)
        elif source != SyncStream.INTERNAL:
            event.client = self
        return super().dispatch_event(event, source)

    async def get_event(self, room_id: RoomID, event_id: EventID) -> Event:
        event = await super().get_event(room_id, event_id)
        if isinstance(event, MessageEvent):
            event.content.trim_reply_fallback()
            return MaubotMessageEvent(event, self)
        else:
            event.client = self
        return event

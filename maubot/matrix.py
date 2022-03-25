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

from typing import Awaitable
from html import escape
import asyncio

import attr

from mautrix.client import Client as MatrixClient, SyncStream
from mautrix.errors import DecryptionError
from mautrix.types import (
    EncryptedEvent,
    Event,
    EventID,
    EventType,
    Format,
    MessageEvent,
    MessageEventContent,
    MessageType,
    RelatesTo,
    RoomID,
    TextMessageEventContent,
)
from mautrix.util import markdown
from mautrix.util.formatter import EntityType, MarkdownString, MatrixParser


class HumanReadableString(MarkdownString):
    def format(self, entity_type: EntityType, **kwargs) -> MarkdownString:
        if entity_type == EntityType.URL and kwargs["url"] != self.text:
            self.text = f"{self.text} ({kwargs['url']})"
            return self
        return super(HumanReadableString, self).format(entity_type, **kwargs)


class MaubotHTMLParser(MatrixParser[HumanReadableString]):
    fs = HumanReadableString


async def parse_formatted(
    message: str, allow_html: bool = False, render_markdown: bool = True
) -> tuple[str, str]:
    if render_markdown:
        html = markdown.render(message, allow_html=allow_html)
    elif allow_html:
        html = message
    else:
        return message, escape(message)
    return (await MaubotHTMLParser().parse(html)).text, html


class MaubotMessageEvent(MessageEvent):
    client: MaubotMatrixClient
    disable_reply: bool

    def __init__(self, base: MessageEvent, client: MaubotMatrixClient):
        super().__init__(
            **{a.name.lstrip("_"): getattr(base, a.name) for a in attr.fields(MessageEvent)}
        )
        self.client = client
        self.disable_reply = client.disable_replies

    async def respond(
        self,
        content: str | MessageEventContent,
        event_type: EventType = EventType.ROOM_MESSAGE,
        markdown: bool = True,
        allow_html: bool = False,
        reply: bool | str = False,
        edits: EventID | MessageEvent | None = None,
    ) -> EventID:
        if isinstance(content, str):
            content = TextMessageEventContent(msgtype=MessageType.NOTICE, body=content)
            if allow_html or markdown:
                content.format = Format.HTML
                content.body, content.formatted_body = await parse_formatted(
                    content.body, render_markdown=markdown, allow_html=allow_html
                )
        if edits:
            content.set_edit(edits)
        elif reply:
            if reply != "force" and self.disable_reply:
                content.body = f"{self.sender}: {content.body}"
                fmt_body = content.formatted_body or escape(content.body).replace("\n", "<br>")
                content.formatted_body = (
                    f'<a href="https://matrix.to/#/{self.sender}">'
                    f"{self.sender}"
                    f"</a>: {fmt_body}"
                )
            else:
                content.set_reply(self)
        return await self.client.send_message_event(self.room_id, event_type, content)

    def reply(
        self,
        content: str | MessageEventContent,
        event_type: EventType = EventType.ROOM_MESSAGE,
        markdown: bool = True,
        allow_html: bool = False,
    ) -> Awaitable[EventID]:
        return self.respond(
            content, event_type, markdown=markdown, reply=True, allow_html=allow_html
        )

    def mark_read(self) -> Awaitable[None]:
        return self.client.send_receipt(self.room_id, self.event_id, "m.read")

    def react(self, key: str) -> Awaitable[EventID]:
        return self.client.react(self.room_id, self.event_id, key)

    def edit(
        self,
        content: str | MessageEventContent,
        event_type: EventType = EventType.ROOM_MESSAGE,
        markdown: bool = True,
        allow_html: bool = False,
    ) -> Awaitable[EventID]:
        return self.respond(
            content, event_type, markdown=markdown, edits=self, allow_html=allow_html
        )


class MaubotMatrixClient(MatrixClient):
    disable_replies: bool

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.disable_replies = False

    async def send_markdown(
        self,
        room_id: RoomID,
        markdown: str,
        *,
        allow_html: bool = False,
        msgtype: MessageType = MessageType.TEXT,
        edits: EventID | MessageEvent | None = None,
        relates_to: RelatesTo | None = None,
        **kwargs,
    ) -> EventID:
        content = TextMessageEventContent(msgtype=msgtype, format=Format.HTML)
        content.body, content.formatted_body = await parse_formatted(
            markdown, allow_html=allow_html
        )
        if relates_to:
            if edits:
                raise ValueError("Can't use edits and relates_to at the same time.")
            content.relates_to = relates_to
        elif edits:
            content.set_edit(edits)
        return await self.send_message(room_id, content, **kwargs)

    def dispatch_event(self, event: Event, source: SyncStream) -> list[asyncio.Task]:
        if isinstance(event, MessageEvent) and not isinstance(event, MaubotMessageEvent):
            event = MaubotMessageEvent(event, self)
        elif source != SyncStream.INTERNAL:
            event.client = self
        return super().dispatch_event(event, source)

    async def get_event(self, room_id: RoomID, event_id: EventID) -> Event:
        evt = await super().get_event(room_id, event_id)
        if isinstance(evt, EncryptedEvent) and self.crypto:
            try:
                self.crypto_log.trace(f"get_event: Decrypting {evt.event_id} in {evt.room_id}...")
                decrypted = await self.crypto.decrypt_megolm_event(evt)
            except DecryptionError as e:
                self.crypto_log.warning(f"get_event: Failed to decrypt {evt.event_id}: {e}")
                return
            self.crypto_log.trace(f"get_event: Decrypted {evt.event_id}: {decrypted}")
            evt = decrypted
        if isinstance(evt, MessageEvent):
            evt.content.trim_reply_fallback()
            return MaubotMessageEvent(evt, self)
        else:
            evt.client = self
        return evt

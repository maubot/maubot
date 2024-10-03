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
    BaseMessageEventContentFuncs,
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
    text = (await MaubotHTMLParser().parse(html)).text
    if len(text) + len(html) > 60000:
        text = text[:100] + "[long message cut off]"
    return text, html


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
        in_thread: bool | None = None,
        edits: EventID | MessageEvent | None = None,
    ) -> EventID:
        """
        Respond to the message.

        Args:
            content: The content to respond with. If this is a string, it will be passed to
                :func:`parse_formatted` with the markdown and allow_html flags.
                Otherwise, the content is used as-is
            event_type: The type of event to send.
            markdown: When content is a string, should it be parsed as markdown?
            allow_html: When content is a string, should it allow raw HTML?
            reply: Should the response be sent as a reply to this event?
            in_thread: Should the response be sent in a thread with this event?
                By default (``None``), the response will be in a thread if this event is in a
                thread. If set to ``False``, the response will never be in a thread. If set to
                ``True``, the response will always be in a thread, creating one with this event as
                the root if necessary.
            edits: An event ID or MessageEvent to edit. If set, the reply and in_thread parameters
                are ignored, as edits can't change the reply or thread status.

        Returns:
            The ID of the response event.
        """
        if isinstance(content, str):
            content = TextMessageEventContent(msgtype=MessageType.NOTICE, body=content)
            if allow_html or markdown:
                content.format = Format.HTML
                content.body, content.formatted_body = await parse_formatted(
                    content.body, render_markdown=markdown, allow_html=allow_html
                )
        if edits:
            content.set_edit(edits)
        if (
            not edits
            and in_thread is not False
            and (
                in_thread
                or (
                    isinstance(self.content, BaseMessageEventContentFuncs)
                    and self.content.get_thread_parent()
                )
            )
        ):
            content.set_thread_parent(self)
        if reply and not edits:
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
        in_thread: bool | None = None,
    ) -> Awaitable[EventID]:
        """
        Reply to the message. The parameters are the same as :meth:`respond`,
        but ``reply`` is always ``True`` and ``edits`` is not supported.

        Args:
            content: The content to respond with. If this is a string, it will be passed to
                :func:`parse_formatted` with the markdown and allow_html flags.
                Otherwise, the content is used as-is
            event_type: The type of event to send.
            markdown: When content is a string, should it be parsed as markdown?
            allow_html: When content is a string, should it allow raw HTML?
            in_thread: Should the response be sent in a thread with this event?
                By default (``None``), the response will be in a thread if this event is in a
                thread. If set to ``False``, the response will never be in a thread. If set to
                ``True``, the response will always be in a thread, creating one with this event as
                the root if necessary.

        Returns:
            The ID of the response event.
        """
        return self.respond(
            content,
            event_type,
            markdown=markdown,
            reply=True,
            in_thread=in_thread,
            allow_html=allow_html,
        )

    def mark_read(self) -> Awaitable[None]:
        """
        Mark this event as read.
        """
        return self.client.send_receipt(self.room_id, self.event_id, "m.read")

    def react(self, key: str) -> Awaitable[EventID]:
        """
        React to this event with the given key.

        Args:
            key: The key to react with. Often an unicode emoji.

        Returns:
            The ID of the reaction event.

        Examples:
            >>> evt: MaubotMessageEvent
            >>> evt.react("🐈️")
        """
        return self.client.react(self.room_id, self.event_id, key)

    def redact(self, reason: str | None = None) -> Awaitable[EventID]:
        """
        Redact this event.

        Args:
            reason: Optionally, the reason for redacting the event.

        Returns:
            The ID of the redaction event.
        """
        return self.client.redact(self.room_id, self.event_id, reason=reason)

    def edit(
        self,
        content: str | MessageEventContent,
        event_type: EventType = EventType.ROOM_MESSAGE,
        markdown: bool = True,
        allow_html: bool = False,
    ) -> Awaitable[EventID]:
        """
        Edit this event. Note that other clients will only render the edit if it was sent by the
        same user who's doing the editing.

        Args:
            content: The new content for the event. If this is a string, it will be passed to
                :func:`parse_formatted` with the markdown and allow_html flags.
                Otherwise, the content is used as-is.
            event_type: The type of event to edit into.
            markdown: When content is a string, should it be parsed as markdown?
            allow_html: When content is a string, should it allow raw HTML?

        Returns:
            The ID of the edit event.
        """
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

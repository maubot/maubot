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
from typing import Awaitable, Union

from mautrix.types import Event as MatrixEvent, EventType, MessageEventContent, MessageType, EventID
from mautrix.client.api.types.event.base import BaseRoomEvent
from mautrix.client import ClientAPI


class FakeEvent(BaseRoomEvent):
    def __new__(cls, *args, **kwargs):
        raise RuntimeError("Can't create instance of type hint header class")

    def respond(self, content: Union[str, MessageEventContent],
                event_type: EventType = EventType.ROOM_MESSAGE) -> Awaitable[EventID]:
        raise RuntimeError("Can't call methods of type hint header class")

    def reply(self, content: Union[str, MessageEventContent],
              event_type: EventType = EventType.ROOM_MESSAGE) -> Awaitable[EventID]:
        raise RuntimeError("Can't call methods of type hint header class")

    def mark_read(self) -> Awaitable[None]:
        raise RuntimeError("Can't call methods of type hint header class")


class Event:
    def __init__(self, client: ClientAPI, target: MatrixEvent):
        self.client: ClientAPI = client
        self.target: MatrixEvent = target

    def __getattr__(self, item):
        return getattr(self.target, item)

    def __setattr__(self, key, value):
        return setattr(self.target, key, value)

    def respond(self, content: Union[str, MessageEventContent],
                event_type: EventType = EventType.ROOM_MESSAGE) -> Awaitable[EventID]:
        if isinstance(content, str):
            content = MessageEventContent(msgtype=MessageType.TEXT, body=content)
        return self.client.send_message_event(self.target.room_id, event_type, content)

    def reply(self, content: Union[str, MessageEventContent],
              event_type: EventType = EventType.ROOM_MESSAGE) -> Awaitable[EventID]:
        if isinstance(content, str):
            content = MessageEventContent(msgtype=MessageType.TEXT, body=content)
        content.set_reply(self.target)
        return self.client.send_message_event(self.target.room_id, event_type, content)

    def mark_read(self) -> Awaitable[None]:
        return self.client.send_receipt(self.target.room_id, self.target.event_id, "m.read")

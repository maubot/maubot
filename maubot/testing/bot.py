# maubot - A plugin-based Matrix bot system.
# Copyright (C) 2023 Aurélien Bompard
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
import asyncio
import time

from attr import dataclass

from maubot.matrix import MaubotMatrixClient, MaubotMessageEvent
from mautrix.api import HTTPAPI
from mautrix.types import (
    EventContent,
    EventType,
    MessageEvent,
    MessageType,
    RoomID,
    TextMessageEventContent,
)


@dataclass
class MatrixEvent:
    room_id: RoomID
    event_type: EventType
    content: EventContent
    kwargs: dict


class TestBot:
    """A mocked bot used for testing purposes.

    Send messages to the mock Matrix server with the ``send()`` method.
    Look into the ``responded`` list to get what server has replied.
    """

    def __init__(self, mxid="@botname:example.com", mxurl="http://matrix.example.com"):
        api = HTTPAPI(base_url=mxurl)
        self.client = MaubotMatrixClient(api=api)
        self.responded = []
        self.client.mxid = mxid
        self.client.send_message_event = self._mock_send_message_event

    async def _mock_send_message_event(self, room_id, event_type, content, txn_id=None, **kwargs):
        self.responded.append(
            MatrixEvent(room_id=room_id, event_type=event_type, content=content, kwargs=kwargs)
        )

    async def dispatch(self, event_type: EventType, event):
        tasks = self.client.dispatch_manual_event(event_type, event, force_synchronous=True)
        return await asyncio.gather(*tasks)

    async def send(
        self,
        content,
        html=None,
        room_id="testroom",
        msg_type=MessageType.TEXT,
        sender="@dummy:example.com",
        timestamp=None,
    ):
        event = make_message(
            content,
            html=html,
            room_id=room_id,
            msg_type=msg_type,
            sender=sender,
            timestamp=timestamp,
        )
        await self.dispatch(EventType.ROOM_MESSAGE, MaubotMessageEvent(event, self.client))


def make_message(
    content,
    html=None,
    room_id="testroom",
    msg_type=MessageType.TEXT,
    sender="@dummy:example.com",
    timestamp=None,
):
    """Make a Matrix message event."""
    return MessageEvent(
        type=EventType.ROOM_MESSAGE,
        room_id=room_id,
        event_id="test",
        sender=sender,
        timestamp=timestamp or int(time.time() * 1000),
        content=TextMessageEventContent(msgtype=msg_type, body=content, formatted_body=html),
    )

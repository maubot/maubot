from maubot import Plugin, MessageEvent
from mautrix.types import EventType


class HelloWorldBot(Plugin):
    async def start(self) -> None:
        self.client.add_event_handler(self.handler, EventType.ROOM_MESSAGE)

    async def stop(self) -> None:
        self.client.remove_event_handler(self.handler, EventType.ROOM_MESSAGE)

    async def handler(self, event: MessageEvent) -> None:
        if event.sender != self.client.mxid:
            await event.reply("Hello, World!")

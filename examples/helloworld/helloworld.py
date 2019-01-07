from mautrix.types import EventType
from maubot import Plugin, MessageEvent
from maubot.handlers import event


class HelloWorldBot(Plugin):
    @event.on(EventType.ROOM_MESSAGE)
    async def handler(self, event: MessageEvent) -> None:
        if event.sender != self.client.mxid:
            await event.reply("Hello, World!")

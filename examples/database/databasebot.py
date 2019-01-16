from typing import Type

from sqlalchemy import Column, String, Text, Table, MetaData, orm, func

from mautrix.types import EventType
from maubot import Plugin, MessageEvent
from maubot.handlers import event, command


class DatabaseBot(Plugin):
    db: orm.Session
    events: Type[Table]

    async def start(self) -> None:
        await super().start()

        db_factory = orm.sessionmaker(bind=self.database)
        self.db = orm.scoped_session(db_factory)
        table_meta = MetaData(bind=self.db)
        self.events = Table("event", table_meta,
                            Column("room_id", String(255), primary_key=True),
                            Column("event_id", String(255), primary_key=True),
                            Column("sender", String(255)),
                            Column("body", Text))
        # In the future, there will be a proper way to include Alembic upgrades in plugins.
        table_meta.create_all()

    @event.on(EventType.ROOM_MESSAGE)
    async def handler(self, event: MessageEvent) -> None:
        self.db.add(self.events(room_id=event.room_id, event_id=event.event_id,
                                sender=event.sender, body=event.content.body))

    @command.new("stats")
    async def find(self, _: MessageEvent) -> None:
        res = (self.db
               .query(func.sum(self.events.event_id))
               .group_by(self.events.room_id, self.events.sender)
               .all())
        print(res)

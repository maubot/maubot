from mautrix.util.async_db import Database

from .client import Client
from .instance import Instance
from .upgrade import upgrade_table


def init(db: Database) -> None:
    for table in (Client, Instance):
        table.db = db


__all__ = ["upgrade_table", "init", "Client", "Instance"]

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
from sqlalchemy import orm
import sqlalchemy as sql
import logging.config
import argparse
import copy

from .config import Config
from .__meta__ import __version__

parser = argparse.ArgumentParser(description="A plugin-based Matrix bot system.",
                                 prog="python -m maubot")
parser.add_argument("-c", "--config", type=str, default="config.yaml",
                    metavar="<path>", help="the path to your config file")
args = parser.parse_args()

config = Config(args.config, args.base_config)
config.load()
config.update()

logging.config.dictConfig(copy.deepcopy(config["logging"]))
log = logging.getLogger("maubot")
log.debug(f"Initializing maubot {__version__}")

db_engine = sql.create_engine(config["database"])
db_factory = orm.sessionmaker(bind=db_engine)
db_session = orm.scoping.scoped_session(db_factory)
Base.metadata.bind=db_engine

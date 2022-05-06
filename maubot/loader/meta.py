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
from typing import List, Optional

from attr import dataclass
from packaging.version import InvalidVersion, Version

from mautrix.types import (
    ExtensibleEnum,
    SerializableAttrs,
    SerializerError,
    deserializer,
    serializer,
)

from ..__meta__ import __version__


@serializer(Version)
def serialize_version(version: Version) -> str:
    return str(version)


@deserializer(Version)
def deserialize_version(version: str) -> Version:
    try:
        return Version(version)
    except InvalidVersion as e:
        raise SerializerError("Invalid version") from e


class DatabaseType(ExtensibleEnum):
    SQLALCHEMY = "sqlalchemy"
    ASYNCPG = "asyncpg"


@dataclass
class PluginMeta(SerializableAttrs):
    id: str
    version: Version
    modules: List[str]
    main_class: str

    maubot: Version = Version(__version__)
    database: bool = False
    database_type: DatabaseType = DatabaseType.SQLALCHEMY
    config: bool = False
    webapp: bool = False
    license: str = ""
    extra_files: List[str] = []
    dependencies: List[str] = []
    soft_dependencies: List[str] = []

    @property
    def database_type_str(self) -> Optional[str]:
        return self.database_type.value if self.database else None

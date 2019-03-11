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
from typing import TypeVar, Type, Dict, Set, List, TYPE_CHECKING
from abc import ABC, abstractmethod
import asyncio

from attr import dataclass
from packaging.version import Version, InvalidVersion
from mautrix.client.api.types.util import (SerializableAttrs, SerializerError, serializer,
                                           deserializer)

from ..__meta__ import __version__
from ..plugin_base import Plugin

if TYPE_CHECKING:
    from ..instance import PluginInstance

PluginClass = TypeVar("PluginClass", bound=Plugin)


class IDConflictError(Exception):
    pass


@serializer(Version)
def serialize_version(version: Version) -> str:
    return str(version)


@deserializer(Version)
def deserialize_version(version: str) -> Version:
    try:
        return Version(version)
    except InvalidVersion as e:
        raise SerializerError("Invalid version") from e


@dataclass
class PluginMeta(SerializableAttrs['PluginMeta']):
    id: str
    version: Version
    modules: List[str]
    main_class: str

    maubot: Version = Version(__version__)
    database: bool = False
    webapp: bool = False
    license: str = ""
    extra_files: List[str] = []
    dependencies: List[str] = []
    soft_dependencies: List[str] = []


class PluginLoader(ABC):
    id_cache: Dict[str, 'PluginLoader'] = {}

    meta: PluginMeta
    references: Set['PluginInstance']

    def __init__(self):
        self.references = set()

    @classmethod
    def find(cls, plugin_id: str) -> 'PluginLoader':
        return cls.id_cache[plugin_id]

    def to_dict(self) -> dict:
        return {
            "id": self.meta.id,
            "version": str(self.meta.version),
            "instances": [instance.to_dict() for instance in self.references],
        }

    @property
    @abstractmethod
    def source(self) -> str:
        pass

    @abstractmethod
    async def read_file(self, path: str) -> bytes:
        pass

    async def stop_instances(self) -> None:
        await asyncio.gather(*[instance.stop() for instance
                               in self.references if instance.started])

    async def start_instances(self) -> None:
        await asyncio.gather(*[instance.start() for instance
                               in self.references if instance.enabled])

    @abstractmethod
    async def load(self) -> Type[PluginClass]:
        pass

    @abstractmethod
    async def reload(self) -> Type[PluginClass]:
        pass

    @abstractmethod
    async def unload(self) -> None:
        pass

    @abstractmethod
    async def delete(self) -> None:
        pass

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

import os
import os.path

from ..loader import BasePluginLoader


class FileSystemLoader(BasePluginLoader):
    def __init__(self, path: str) -> None:
        self.path = path

    @property
    def source(self) -> str:
        return self.path

    def sync_read_file(self, path: str) -> bytes:
        with open(os.path.join(self.path, path), "rb") as file:
            return file.read()

    async def read_file(self, path: str) -> bytes:
        return self.sync_read_file(path)

    def sync_list_files(self, directory: str) -> list[str]:
        return os.listdir(os.path.join(self.path, directory))

    async def list_files(self, directory: str) -> list[str]:
        return self.sync_list_files(directory)

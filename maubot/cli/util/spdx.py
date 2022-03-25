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

import json
import zipfile

import pkg_resources

spdx_list: dict[str, dict[str, str]] | None = None


def load() -> None:
    global spdx_list
    if spdx_list is not None:
        return
    with pkg_resources.resource_stream("maubot.cli", "res/spdx.json.zip") as disk_file:
        with zipfile.ZipFile(disk_file) as zip_file:
            with zip_file.open("spdx.json") as file:
                spdx_list = json.load(file)


def get(id: str) -> dict[str, str]:
    if not spdx_list:
        load()
    return spdx_list[id.lower()]


def valid(id: str) -> bool:
    if not spdx_list:
        load()
    return id.lower() in spdx_list

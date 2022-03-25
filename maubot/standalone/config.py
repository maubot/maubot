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
from typing import Any
import os

from mautrix.util.config import BaseFileConfig, ConfigUpdateHelper


class Config(BaseFileConfig):
    def __getitem__(self, key: str) -> Any:
        try:
            return os.environ[f"MAUBOT_{key.replace('.', '_').upper()}"]
        except KeyError:
            return super().__getitem__(key)

    def do_update(self, helper: ConfigUpdateHelper) -> None:
        copy, _, base = helper
        copy("user.credentials.id")
        copy("user.credentials.homeserver")
        copy("user.credentials.access_token")
        copy("user.credentials.device_id")
        copy("user.sync")
        copy("user.autojoin")
        copy("user.displayname")
        copy("user.avatar_url")
        if "server" in base:
            copy("server.hostname")
            copy("server.port")
            copy("server.base_path")
            copy("server.public_url")
        copy("database")
        copy("database_opts")
        if "plugin_config" in base:
            copy("plugin_config")
        copy("logging")

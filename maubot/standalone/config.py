# maubot - A plugin-based Matrix bot system.
# Copyright (C) 2019 Tulir Asokan
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
from mautrix.util.config import BaseFileConfig, ConfigUpdateHelper


class Config(BaseFileConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        copy, _, base = helper
        copy("user.credentials.id")
        copy("user.credentials.homeserver")
        copy("user.credentials.access_token")
        copy("user.sync")
        copy("user.autojoin")
        copy("user.displayname")
        copy("user.avatar_url")
        if "database" in base:
            copy("database")
        if "plugin_config" in base:
            copy("plugin_config")
        if "server" in base:
            copy("server.hostname")
            copy("server.port")
            copy("server.public_url")
        copy("logging")

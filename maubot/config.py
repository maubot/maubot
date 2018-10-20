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
import random
import string

from mautrix.util import BaseFileConfig


class Config(BaseFileConfig):
    @staticmethod
    def _new_token() -> str:
        return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(64))

    def update(self):
        base, copy, copy_dict = self._pre_update()
        copy("database")
        copy("plugin_directories")
        copy("server.hostname")
        copy("server.port")
        copy("server.listen")
        copy("server.base_path")
        shared_secret = self["server.shared_secret"]
        if shared_secret is None or shared_secret == "generate":
            base["server.shared_secret"] = self._new_token()
        else:
            base["server.shared_secret"] = shared_secret
        copy("logging")

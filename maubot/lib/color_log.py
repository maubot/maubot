# maubot - A plugin-based Matrix bot system.
# Copyright (C) 2020 Tulir Asokan
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
from mautrix.util.logging.color import (ColorFormatter as BaseColorFormatter, PREFIX, MAU_COLOR,
                                        MXID_COLOR, RESET)

INST_COLOR = PREFIX + "35m"  # magenta
LOADER_COLOR = PREFIX + "36m"  # blue


class ColorFormatter(BaseColorFormatter):
    def _color_name(self, module: str) -> str:
        client = "maubot.client"
        if module.startswith(client):
            return f"{MAU_COLOR}{client}{RESET}.{MXID_COLOR}{module[len(client) + 1:]}{RESET}"
        instance = "maubot.instance"
        if module.startswith(instance):
            return f"{MAU_COLOR}{instance}{RESET}.{INST_COLOR}{module[len(instance) + 1:]}{RESET}"
        loader = "maubot.loader"
        if module.startswith(loader):
            return f"{MAU_COLOR}{instance}{RESET}.{LOADER_COLOR}{module[len(loader) + 1:]}{RESET}"
        if module.startswith("maubot"):
            return f"{MAU_COLOR}{module}{RESET}"
        return super()._color_name(module)

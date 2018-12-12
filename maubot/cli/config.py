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
import json
import os

config = {
    "servers": {}
}
configdir = os.environ.get("XDG_CONFIG_HOME", os.path.join(os.environ.get("HOME"), ".config"))


def save_config() -> None:
    with open(f"{configdir}/maubot-cli.json", "w") as file:
        json.dump(config, file)


def load_config() -> None:
    try:
        with open(f"{configdir}/maubot-cli.json") as file:
            loaded = json.load(file)
            config["servers"] = loaded["servers"]
    except FileNotFoundError:
        pass

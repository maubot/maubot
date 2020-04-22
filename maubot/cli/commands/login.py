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
from urllib.request import urlopen
from urllib.error import HTTPError
import json
import os

from colorama import Fore

from ..config import save_config, config
from ..cliq import cliq


@cliq.command(help="Log in to a Maubot instance")
@cliq.option("-u", "--username", help="The username of your account", default=os.environ.get("USER", None), required=True)
@cliq.option("-p", "--password", help="The password to your account", inq_type="password", required=True)
@cliq.option("-s", "--server", help="The server to log in to", default="http://localhost:29316", required=True)
@cliq.option("-a", "--alias", help="Alias to reference the server without typing the full URL", default="", required=False)
def login(server, username, password, alias) -> None:
    data = {
        "username": username,
        "password": password,
    }
    try:
        with urlopen(f"{server}/_matrix/maubot/v1/auth/login",
                     data=json.dumps(data).encode("utf-8")) as resp_data:
            resp = json.load(resp_data)
            config["servers"][server] = resp["token"]
            if not config["default_server"]:
                print(Fore.CYAN, "Setting", server, "as the default server")
                config["default_server"] = server
            if alias:
                config["aliases"][alias] = server
            save_config()
            print(Fore.GREEN + "Logged in successfully")
    except HTTPError as e:
        try:
            err = json.load(e)
        except json.JSONDecodeError:
            err = {}
        print(Fore.RED + err.get("error", str(e)) + Fore.RESET)

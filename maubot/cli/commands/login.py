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
from urllib.request import urlopen
from urllib.error import HTTPError
import click
import json
import os

from colorama import Fore, Style

from maubot.cli.base import app
from maubot.cli.config import save_config, config


@app.command(help="Log in to a Maubot instance")
@click.argument("server", required=True, default="http://localhost:29316")
@click.option("-u", "--username", help="The username of your account", prompt=True,
              default=lambda: os.environ.get('USER', ''), show_default="current user")
@click.password_option("-p", "--password", help="The password to your account", required=True,
                       confirmation_prompt=False)
def login(server, username, password) -> None:
    data = {
        "username": username,
        "password": password,
    }
    try:
        with urlopen(f"{server}/_matrix/maubot/v1/auth/login",
                     data=json.dumps(data).encode("utf-8")) as resp_data:
            resp = json.load(resp_data)
            config["servers"][server] = resp["token"]
            save_config()
            print(Fore.GREEN, "Logged in successfully")
    except HTTPError as e:
        if e.code == 401:
            print(Fore.RED + "Invalid username or password" + Style.RESET_ALL)

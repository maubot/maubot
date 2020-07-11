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
from urllib.parse import quote
from urllib.request import urlopen, Request
from urllib.error import HTTPError
import functools
import json

from colorama import Fore
import click

from ..config import get_token
from ..cliq import cliq

history_count: int = 10

enc = functools.partial(quote, safe="")

friendly_errors = {
    "server_not_found": "Registration target server not found.\n\n"
                        "To log in or register through maubot, you must add the server to the\n"
                        "registration_secrets section in the config. If you only want to log in,\n"
                        "leave the `secret` field empty."
}


@cliq.command(help="Log into a Matrix account via the Maubot server")
@cliq.option("-h", "--homeserver", help="The homeserver to log into", required_unless="list")
@cliq.option("-u", "--username", help="The username to log in with", required_unless="list")
@cliq.option("-p", "--password", help="The password to log in with", inq_type="password",
             required_unless="list")
@cliq.option("-s", "--server", help="The maubot instance to log in through", default="",
             required=False, prompt=False)
@click.option("-r", "--register", help="Register instead of logging in", is_flag=True,
              default=False)
@click.option("-l", "--list", help="List available homeservers", is_flag=True, default=False)
def auth(homeserver: str, username: str, password: str, server: str, register: bool, list: bool
         ) -> None:
    server, token = get_token(server)
    if not token:
        return
    headers = {"Authorization": f"Bearer {token}"}
    if list:
        url = f"{server}/_matrix/maubot/v1/client/auth/servers"
        with urlopen(Request(url, headers=headers)) as resp_data:
            resp = json.load(resp_data)
            print(f"{Fore.GREEN}Available Matrix servers for registration and login:{Fore.RESET}")
            for server in resp.keys():
                print(f"* {Fore.CYAN}{server}{Fore.RESET}")
            return
    endpoint = "register" if register else "login"
    headers["Content-Type"] = "application/json"
    url = f"{server}/_matrix/maubot/v1/client/auth/{enc(homeserver)}/{endpoint}"
    req = Request(url, headers=headers,
                  data=json.dumps({
                      "username": username,
                      "password": password,
                  }).encode("utf-8"))
    try:
        with urlopen(req) as resp_data:
            resp = json.load(resp_data)
            action = "registered" if register else "logged in as"
            print(f"{Fore.GREEN}Successfully {action} "
                  f"{Fore.CYAN}{resp['user_id']}{Fore.GREEN}.")
            print(f"{Fore.GREEN}Access token: {Fore.CYAN}{resp['access_token']}{Fore.RESET}")
            print(f"{Fore.GREEN}Device ID: {Fore.CYAN}{resp['device_id']}{Fore.RESET}")
    except HTTPError as e:
        try:
            err_data = json.load(e)
            error = friendly_errors.get(err_data["errcode"], err_data["error"])
        except (json.JSONDecodeError, KeyError):
            error = str(e)
        action = "register" if register else "log in"
        print(f"{Fore.RED}Failed to {action}: {error}{Fore.RESET}")

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
import json

from colorama import Fore
from yarl import URL
import aiohttp
import click

from ..config import get_token
from ..cliq import cliq

history_count: int = 10

friendly_errors = {
    "server_not_found": "Registration target server not found.\n\n"
                        "To log in or register through maubot, you must add the server to the\n"
                        "homeservers section in the config. If you only want to log in,\n"
                        "leave the `secret` field empty."
}


async def list_servers(server: str, sess: aiohttp.ClientSession) -> None:
    url = URL(server) / "_matrix/maubot/v1/client/auth/servers"
    async with sess.get(url) as resp:
        data = await resp.json()
        print(f"{Fore.GREEN}Available Matrix servers for registration and login:{Fore.RESET}")
        for server in data.keys():
            print(f"* {Fore.CYAN}{server}{Fore.RESET}")


@cliq.command(help="Log into a Matrix account via the Maubot server")
@cliq.option("-h", "--homeserver", help="The homeserver to log into", required_unless="list")
@cliq.option("-u", "--username", help="The username to log in with", required_unless="list")
@cliq.option("-p", "--password", help="The password to log in with", inq_type="password",
             required_unless="list")
@cliq.option("-s", "--server", help="The maubot instance to log in through", default="",
             required=False, prompt=False)
@click.option("-r", "--register", help="Register instead of logging in", is_flag=True,
              default=False)
@click.option("-c", "--update-client", help="Instead of returning the access token, "
                                            "create or update a client in maubot using it",
              is_flag=True, default=False)
@click.option("-l", "--list", help="List available homeservers", is_flag=True, default=False)
@cliq.with_authenticated_http
async def auth(homeserver: str, username: str, password: str, server: str, register: bool,
               list: bool, update_client: bool, sess: aiohttp.ClientSession) -> None:
    if list:
        await list_servers(server, sess)
        return
    endpoint = "register" if register else "login"
    url = URL(server) / "_matrix/maubot/v1/client/auth" / homeserver / endpoint
    if update_client:
        url = url.with_query({"update_client": "true"})
    req_data = {"username": username, "password": password}

    async with sess.post(url, json=req_data) as resp:
        if resp.status == 200:
            data = await resp.json()
            action = "registered" if register else "logged in as"
            print(f"{Fore.GREEN}Successfully {action} {Fore.CYAN}{data['user_id']}{Fore.GREEN}.")
            print(f"{Fore.GREEN}Access token: {Fore.CYAN}{data['access_token']}{Fore.RESET}")
            print(f"{Fore.GREEN}Device ID: {Fore.CYAN}{data['device_id']}{Fore.RESET}")
        elif resp.status in (201, 202):
            data = await resp.json()
            action = "created" if resp.status == 201 else "updated"
            print(f"{Fore.GREEN}Successfully {action} client for "
                  f"{Fore.CYAN}{data['id']}{Fore.GREEN} / "
                  f"{Fore.CYAN}{data['device_id']}{Fore.GREEN}.{Fore.RESET}")
        else:
            try:
                err_data = await resp.json()
                error = friendly_errors.get(err_data["errcode"], err_data["error"])
            except (aiohttp.ContentTypeError, json.JSONDecodeError, KeyError):
                error = await resp.text()
            action = "register" if register else "log in"
            print(f"{Fore.RED}Failed to {action}: {error}{Fore.RESET}")

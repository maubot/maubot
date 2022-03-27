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
import json
import webbrowser

from colorama import Fore
from yarl import URL
import aiohttp
import click

from ..cliq import cliq

history_count: int = 10

friendly_errors = {
    "server_not_found": (
        "Registration target server not found.\n\n"
        "To log in or register through maubot, you must add the server to the\n"
        "homeservers section in the config. If you only want to log in,\n"
        "leave the `secret` field empty."
    ),
    "registration_no_sso": (
        "The register operation is only for registering with a password.\n\n"
        "To register with SSO, simply leave out the --register flag."
    ),
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
@cliq.option(
    "-u", "--username", help="The username to log in with", required_unless=["list", "sso"]
)
@cliq.option(
    "-p",
    "--password",
    help="The password to log in with",
    inq_type="password",
    required_unless=["list", "sso"],
)
@cliq.option(
    "-s",
    "--server",
    help="The maubot instance to log in through",
    default="",
    required=False,
    prompt=False,
)
@click.option(
    "-r", "--register", help="Register instead of logging in", is_flag=True, default=False
)
@click.option(
    "-c",
    "--update-client",
    help="Instead of returning the access token, create or update a client in maubot using it",
    is_flag=True,
    default=False,
)
@click.option("-l", "--list", help="List available homeservers", is_flag=True, default=False)
@click.option(
    "-o", "--sso", help="Use single sign-on instead of password login", is_flag=True, default=False
)
@click.option(
    "-n",
    "--device-name",
    help="The initial e2ee device displayname (only for login)",
    default="Maubot",
    required=False,
)
@cliq.with_authenticated_http
async def auth(
    homeserver: str,
    username: str,
    password: str,
    server: str,
    register: bool,
    list: bool,
    update_client: bool,
    device_name: str,
    sso: bool,
    sess: aiohttp.ClientSession,
) -> None:
    if list:
        await list_servers(server, sess)
        return
    endpoint = "register" if register else "login"
    url = URL(server) / "_matrix/maubot/v1/client/auth" / homeserver / endpoint
    if update_client:
        url = url.update_query({"update_client": "true"})
    if sso:
        url = url.update_query({"sso": "true"})
        req_data = {"device_name": device_name}
    else:
        req_data = {"username": username, "password": password, "device_name": device_name}

    async with sess.post(url, json=req_data) as resp:
        if not 200 <= resp.status < 300:
            await print_error(resp, is_register=register)
        elif sso:
            await wait_sso(resp, sess, server, homeserver)
        else:
            await print_response(resp, is_register=register)


async def wait_sso(
    resp: aiohttp.ClientResponse, sess: aiohttp.ClientSession, server: str, homeserver: str
) -> None:
    data = await resp.json()
    sso_url, reg_id = data["sso_url"], data["id"]
    print(f"{Fore.GREEN}Opening {Fore.CYAN}{sso_url}{Fore.RESET}")
    webbrowser.open(sso_url, autoraise=True)
    print(f"{Fore.GREEN}Waiting for login token...{Fore.RESET}")
    wait_url = URL(server) / "_matrix/maubot/v1/client/auth" / homeserver / "sso" / reg_id / "wait"
    async with sess.post(wait_url, json={}) as resp:
        await print_response(resp, is_register=False)


async def print_response(resp: aiohttp.ClientResponse, is_register: bool) -> None:
    if resp.status == 200:
        data = await resp.json()
        action = "registered" if is_register else "logged in as"
        print(f"{Fore.GREEN}Successfully {action} {Fore.CYAN}{data['user_id']}{Fore.GREEN}.")
        print(f"{Fore.GREEN}Access token: {Fore.CYAN}{data['access_token']}{Fore.RESET}")
        print(f"{Fore.GREEN}Device ID: {Fore.CYAN}{data['device_id']}{Fore.RESET}")
    elif resp.status in (201, 202):
        data = await resp.json()
        action = "created" if resp.status == 201 else "updated"
        print(
            f"{Fore.GREEN}Successfully {action} client for "
            f"{Fore.CYAN}{data['id']}{Fore.GREEN} / "
            f"{Fore.CYAN}{data['device_id']}{Fore.GREEN}.{Fore.RESET}"
        )
    else:
        await print_error(resp, is_register)


async def print_error(resp: aiohttp.ClientResponse, is_register: bool) -> None:
    try:
        err_data = await resp.json()
        error = friendly_errors.get(err_data["errcode"], err_data["error"])
    except (aiohttp.ContentTypeError, json.JSONDecodeError, KeyError):
        error = await resp.text()
    action = "register" if is_register else "log in"
    print(f"{Fore.RED}Failed to {action}: {error}{Fore.RESET}")

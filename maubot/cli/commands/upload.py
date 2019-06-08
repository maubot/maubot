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
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from typing import IO
import json

from colorama import Fore
import click

from ..base import app
from ..config import get_default_server, get_token


class UploadError(Exception):
    pass


@app.command(help="Upload a maubot plugin")
@click.argument("path")
@click.option("-s", "--server", help="The maubot instance to upload the plugin to")
def upload(path: str, server: str) -> None:
    server, token = get_token(server)
    if not token:
        return
    with open(path, "rb") as file:
        upload_file(file, server, token)


def upload_file(file: IO, server: str, token: str) -> None:
    req = Request(f"{server}/_matrix/maubot/v1/plugins/upload?allow_override=true", data=file,
                  headers={"Authorization": f"Bearer {token}", "Content-Type": "application/zip"})
    try:
        with urlopen(req) as resp_data:
            resp = json.load(resp_data)
            print(f"{Fore.GREEN}Plugin {Fore.CYAN}{resp['id']} v{resp['version']}{Fore.GREEN} "
                  f"uploaded to {Fore.CYAN}{server}{Fore.GREEN} successfully.{Fore.RESET}")
    except HTTPError as e:
        try:
            err = json.load(e)
        except json.JSONDecodeError:
            err = {}
        print(err.get("stacktrace", ""))
        print(Fore.RED + "Failed to upload plugin: " + err.get("error", str(e)) + Fore.RESET)

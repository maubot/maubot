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
from typing import IO
import json

from colorama import Fore
from yarl import URL
import aiohttp
import click

from ..cliq import cliq


class UploadError(Exception):
    pass


@cliq.command(help="Upload a maubot plugin")
@click.argument("path")
@click.option("-s", "--server", help="The maubot instance to upload the plugin to")
@cliq.with_authenticated_http
async def upload(path: str, server: str, sess: aiohttp.ClientSession) -> None:
    with open(path, "rb") as file:
        await upload_file(sess, file, server)


async def upload_file(sess: aiohttp.ClientSession, file: IO, server: str) -> None:
    url = (URL(server) / "_matrix/maubot/v1/plugins/upload").with_query({"allow_override": "true"})
    headers = {"Content-Type": "application/zip"}
    async with sess.post(url, data=file, headers=headers) as resp:
        if resp.status in (200, 201):
            data = await resp.json()
            print(
                f"{Fore.GREEN}Plugin {Fore.CYAN}{data['id']} v{data['version']}{Fore.GREEN} "
                f"uploaded to {Fore.CYAN}{server}{Fore.GREEN} successfully.{Fore.RESET}"
            )
        else:
            try:
                err = await resp.json()
                if "stacktrace" in err:
                    print(err["stacktrace"])
                err = err["error"]
            except (aiohttp.ContentTypeError, json.JSONDecodeError, KeyError):
                err = await resp.text()
            print(f"{Fore.RED}Failed to upload plugin: {err}{Fore.RESET}")

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
from datetime import datetime
import asyncio

from colorama import Fore
from aiohttp import WSMsgType, WSMessage, ClientSession
from mautrix.client.api.types.util import Obj
import click

from ..config import get_token, get_default_server
from ..base import app

history_count: int = 10


@app.command(help="View the logs of a server")
@click.argument("server", required=False)
@click.option("-t", "--tail", default=10, help="Maximum number of old log lines to display")
def logs(server: str, tail: int) -> None:
    if not server:
        server, token = get_default_server()
    else:
        token = get_token(server)
    if not token:
        return
    global history_count
    history_count = tail
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(view_logs(server, token), loop=loop)
    try:
        loop.run_until_complete(future)
    except KeyboardInterrupt:
        future.cancel()
        loop.run_until_complete(future)
        loop.close()


def parsedate(entry: Obj) -> None:
    i = entry.time.index("+")
    i = entry.time.index(":", i)
    entry.time = entry.time[:i] + entry.time[i + 1:]
    entry.time = datetime.strptime(entry.time, "%Y-%m-%dT%H:%M:%S.%f%z")


levelcolors = {
    "DEBUG": "",
    "INFO": Fore.CYAN,
    "WARNING": Fore.YELLOW,
    "ERROR": Fore.RED,
    "FATAL": Fore.MAGENTA,
}


def print_entry(entry: dict) -> None:
    entry = Obj(**entry)
    parsedate(entry)
    print("{levelcolor}[{date}] [{level}@{logger}] {message}{resetcolor}"
          .format(date=entry.time.strftime("%Y-%m-%d %H:%M:%S"),
                  level=entry.levelname,
                  levelcolor=levelcolors.get(entry.levelname, ""),
                  resetcolor=Fore.RESET,
                  logger=entry.name,
                  message=entry.msg))
    if entry.exc_info:
        print(entry.exc_info)


def handle_msg(data: dict) -> bool:
    if "auth_success" in data:
        if data["auth_success"]:
            print(Fore.GREEN + "Connected to log websocket" + Fore.RESET)
        else:
            print(Fore.RED + "Failed to authenticate to log websocket" + Fore.RESET)
            return False
    elif "history" in data:
        for entry in data["history"][-history_count:]:
            print_entry(entry)
    else:
        print_entry(data)
    return True


async def view_logs(server: str, token: str) -> None:
    async with ClientSession() as session:
        async with session.ws_connect(f"{server}/_matrix/maubot/v1/logs") as ws:
            await ws.send_str(token)
            try:
                msg: WSMessage
                async for msg in ws:
                    if msg.type == WSMsgType.TEXT:
                        if not handle_msg(msg.json()):
                            break
                    elif msg.type == WSMsgType.ERROR:
                        print(Fore.YELLOW + "Connection error: " + msg.data + Fore.RESET)
                    elif msg.type == WSMsgType.CLOSE:
                        print(Fore.YELLOW + "Server closed connection" + Fore.RESET)
            except asyncio.CancelledError:
                pass

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
from string import Template
from subprocess import run
import re

from ruamel.yaml import YAML
from aiohttp import web

from .base import routes

enabled = False


@routes.get("/debug/open")
async def check_enabled(_: web.Request) -> web.Response:
    return web.json_response({
        "enabled": enabled,
    })


try:
    yaml = YAML()

    with open(".dev-open-cfg.yaml", "r") as file:
        cfg = yaml.load(file)
    editor_command = Template(cfg["editor"])
    pathmap = [(re.compile(item["find"]), item["replace"]) for item in cfg["pathmap"]]


    @routes.post("/debug/open")
    async def open_file(request: web.Request) -> web.Response:
        data = await request.json()
        try:
            path = data["path"]
            for find, replace in pathmap:
                path = find.sub(replace, path)
            cmd = editor_command.substitute(path=path, line=data["line"])
        except (KeyError, ValueError):
            return web.Response(status=400)
        res = run(cmd, shell=True)
        return web.json_response({
            "return": res.returncode,
            "stdout": res.stdout,
            "stderr": res.stderr
        })


    enabled = True
except Exception:
    pass

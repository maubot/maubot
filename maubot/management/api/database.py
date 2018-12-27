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
from typing import TYPE_CHECKING

from aiohttp import web
from sqlalchemy import Table, Column

from ...instance import PluginInstance
from .base import routes
from .responses import resp


@routes.get("/instance/{id}/database")
async def get_database(request: web.Request) -> web.Response:
    instance_id = request.match_info.get("id", "")
    instance = PluginInstance.get(instance_id, None)
    if not instance:
        return resp.instance_not_found
    elif not instance.inst_db:
        return resp.plugin_has_no_database
    if TYPE_CHECKING:
        table: Table
        column: Column
    return web.json_response({
        table.name: {
            "columns": {
                column.name: {
                    "type": str(column.type),
                    "unique": column.unique or False,
                    "default": column.default,
                    "nullable": column.nullable,
                    "primary": column.primary_key,
                    "autoincrement": column.autoincrement,
                } for column in table.columns
            },
        } for table in instance.get_db_tables().values()
    })


@routes.get("/instance/{id}/database/{table}")
async def get_table(request: web.Request) -> web.Response:
    instance_id = request.match_info.get("id", "")
    instance = PluginInstance.get(instance_id, None)
    if not instance:
        return resp.instance_not_found
    elif not instance.inst_db:
        return resp.plugin_has_no_database
    tables = instance.get_db_tables()

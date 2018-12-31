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
from typing import Union, TYPE_CHECKING
from datetime import datetime

from aiohttp import web
from sqlalchemy import Table, Column, asc, desc, exc
from sqlalchemy.orm import Query
from sqlalchemy.engine.result import ResultProxy, RowProxy

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


def check_type(val):
    if isinstance(val, datetime):
        return val.isoformat()
    return val


@routes.get("/instance/{id}/database/{table}")
async def get_table(request: web.Request) -> web.Response:
    instance_id = request.match_info.get("id", "")
    instance = PluginInstance.get(instance_id, None)
    if not instance:
        return resp.instance_not_found
    elif not instance.inst_db:
        return resp.plugin_has_no_database
    tables = instance.get_db_tables()
    try:
        table = tables[request.match_info.get("table", "")]
    except KeyError:
        return resp.table_not_found
    try:
        order = [tuple(order.split(":")) for order in request.query.getall("order")]
        order = [(asc if sort.lower() == "asc" else desc)(table.columns[column])
                 if sort else table.columns[column]
                 for column, sort in order]
    except KeyError:
        order = []
    limit = int(request.query.get("limit", 100))
    return execute_query(instance, table.select().order_by(*order).limit(limit))


@routes.post("/instance/{id}/database/query")
async def query(request: web.Request) -> web.Response:
    instance_id = request.match_info.get("id", "")
    instance = PluginInstance.get(instance_id, None)
    if not instance:
        return resp.instance_not_found
    elif not instance.inst_db:
        return resp.plugin_has_no_database
    data = await request.json()
    try:
        sql_query = data["query"]
    except KeyError:
        return resp.query_missing
    return execute_query(instance, sql_query,
                         rows_as_dict=data.get("rows_as_dict", False))


def execute_query(instance: PluginInstance, sql_query: Union[str, Query],
                  rows_as_dict: bool = False) -> web.Response:
    try:
        res: ResultProxy = instance.inst_db.execute(sql_query)
    except exc.IntegrityError as e:
        return resp.sql_integrity_error(e, sql_query)
    except exc.OperationalError as e:
        return resp.sql_operational_error(e, sql_query)
    data = {
        "ok": True,
        "query": str(sql_query),
    }
    if res.returns_rows:
        row: RowProxy
        data["rows"] = [({key: check_type(value) for key, value in row.items()}
                         if rows_as_dict
                         else [check_type(value) for value in row])
                        for row in res]
        data["columns"] = res.keys()
    else:
        data["rowcount"] = res.rowcount
    if res.is_insert:
        data["inserted_primary_key"] = res.inserted_primary_key
    return web.json_response(data)

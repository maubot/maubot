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
from __future__ import annotations

from datetime import datetime

from aiohttp import web
from asyncpg import PostgresError
from sqlalchemy import asc, desc, engine, exc
import aiosqlite

from mautrix.util.async_db import Database

from ...instance import PluginInstance
from .base import routes
from .responses import resp


@routes.get("/instance/{id}/database")
async def get_database(request: web.Request) -> web.Response:
    instance_id = request.match_info["id"].lower()
    instance = await PluginInstance.get(instance_id)
    if not instance:
        return resp.instance_not_found
    elif not instance.inst_db:
        return resp.plugin_has_no_database
    return web.json_response(await instance.get_db_tables())


@routes.get("/instance/{id}/database/{table}")
async def get_table(request: web.Request) -> web.Response:
    instance_id = request.match_info["id"].lower()
    instance = await PluginInstance.get(instance_id)
    if not instance:
        return resp.instance_not_found
    elif not instance.inst_db:
        return resp.plugin_has_no_database
    tables = await instance.get_db_tables()
    try:
        table = tables[request.match_info.get("table", "")]
    except KeyError:
        return resp.table_not_found
    try:
        order = [tuple(order.split(":")) for order in request.query.getall("order")]
        order = [
            (asc if sort.lower() == "asc" else desc)(table.columns[column])
            if sort
            else table.columns[column]
            for column, sort in order
        ]
    except KeyError:
        order = []
    limit = int(request.query.get("limit", "100"))
    if isinstance(instance.inst_db, engine.Engine):
        return _execute_query_sqlalchemy(instance, table.select().order_by(*order).limit(limit))


@routes.post("/instance/{id}/database/query")
async def query(request: web.Request) -> web.Response:
    instance_id = request.match_info["id"].lower()
    instance = await PluginInstance.get(instance_id)
    if not instance:
        return resp.instance_not_found
    elif not instance.inst_db:
        return resp.plugin_has_no_database
    data = await request.json()
    try:
        sql_query = data["query"]
    except KeyError:
        return resp.query_missing
    rows_as_dict = data.get("rows_as_dict", False)
    if isinstance(instance.inst_db, engine.Engine):
        return _execute_query_sqlalchemy(instance, sql_query, rows_as_dict)
    elif isinstance(instance.inst_db, Database):
        try:
            return await _execute_query_asyncpg(instance, sql_query, rows_as_dict)
        except (PostgresError, aiosqlite.Error) as e:
            return resp.sql_error(e, sql_query)
    else:
        return resp.unsupported_plugin_database


def check_type(val):
    if isinstance(val, datetime):
        return val.isoformat()
    return val


async def _execute_query_asyncpg(
    instance: PluginInstance, sql_query: str, rows_as_dict: bool = False
) -> web.Response:
    data = {"ok": True, "query": sql_query}
    if sql_query.upper().startswith("SELECT"):
        res = await instance.inst_db.fetch(sql_query)
        data["rows"] = [
            (
                {key: check_type(value) for key, value in row.items()}
                if rows_as_dict
                else [check_type(value) for value in row]
            )
            for row in res
        ]
        if len(res) > 0:
            # TODO can we find column names when there are no rows?
            data["columns"] = list(res[0].keys())
    else:
        res = await instance.inst_db.execute(sql_query)
        if isinstance(res, str):
            data["status_msg"] = res
        elif isinstance(res, aiosqlite.Cursor):
            data["rowcount"] = res.rowcount
            # data["inserted_primary_key"] = res.lastrowid
        else:
            data["status_msg"] = "unknown status"
    return web.json_response(data)


def _execute_query_sqlalchemy(
    instance: PluginInstance, sql_query: str, rows_as_dict: bool = False
) -> web.Response:
    assert isinstance(instance.inst_db, engine.Engine)
    try:
        res = instance.inst_db.execute(sql_query)
    except exc.IntegrityError as e:
        return resp.sql_integrity_error(e, sql_query)
    except exc.OperationalError as e:
        return resp.sql_operational_error(e, sql_query)
    data = {
        "ok": True,
        "query": str(sql_query),
    }
    if res.returns_rows:
        data["rows"] = [
            (
                {key: check_type(value) for key, value in row.items()}
                if rows_as_dict
                else [check_type(value) for value in row]
            )
            for row in res
        ]
        data["columns"] = res.keys()
    else:
        data["rowcount"] = res.rowcount
    if res.is_insert:
        data["inserted_primary_key"] = res.inserted_primary_key
    return web.json_response(data)

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
from json import JSONDecodeError
from http import HTTPStatus

from aiohttp import web

from ...db import DBPlugin
from ...instance import PluginInstance
from ...loader import PluginLoader
from ...client import Client
from .base import routes
from .responses import resp


@routes.get("/instances")
async def get_instances(_: web.Request) -> web.Response:
    return resp.found([instance.to_dict() for instance in PluginInstance.cache.values()])


@routes.get("/instance/{id}")
async def get_instance(request: web.Request) -> web.Response:
    instance_id = request.match_info.get("id", "").lower()
    instance = PluginInstance.get(instance_id, None)
    if not instance:
        return resp.instance_not_found
    return resp.found(instance.to_dict())


async def _create_instance(instance_id: str, data: dict) -> web.Response:
    plugin_type = data.get("type", None)
    primary_user = data.get("primary_user", None)
    if not plugin_type:
        return resp.plugin_type_required
    elif not primary_user:
        return resp.primary_user_required
    elif not Client.get(primary_user):
        return resp.primary_user_not_found
    try:
        PluginLoader.find(plugin_type)
    except KeyError:
        return resp.plugin_type_not_found
    db_instance = DBPlugin(id=instance_id, type=plugin_type, enabled=data.get("enabled", True),
                           primary_user=primary_user, config=data.get("config", ""))
    instance = PluginInstance(db_instance)
    instance.load()
    PluginInstance.db.add(db_instance)
    PluginInstance.db.commit()
    await instance.start()
    return resp.created(instance.to_dict())


async def _update_instance(instance: PluginInstance, data: dict) -> web.Response:
    if not await instance.update_primary_user(data.get("primary_user", None)):
        return resp.primary_user_not_found
    instance.update_id(data.get("id", None))
    instance.update_enabled(data.get("enabled", None))
    instance.update_config(data.get("config", None))
    await instance.update_started(data.get("started", None))
    await instance.update_type(data.get("type", None))
    instance.db.commit()
    return resp.updated(instance.to_dict())


@routes.put("/instance/{id}")
async def update_instance(request: web.Request) -> web.Response:
    instance_id = request.match_info.get("id", "").lower()
    instance = PluginInstance.get(instance_id, None)
    try:
        data = await request.json()
    except JSONDecodeError:
        return resp.body_not_json
    if not instance:
        return await _create_instance(instance_id, data)
    else:
        return await _update_instance(instance, data)


@routes.delete("/instance/{id}")
async def delete_instance(request: web.Request) -> web.Response:
    instance_id = request.match_info.get("id", "").lower()
    instance = PluginInstance.get(instance_id, None)
    if not instance:
        return resp.instance_not_found
    if instance.started:
        await instance.stop()
    instance.delete()
    return resp.deleted

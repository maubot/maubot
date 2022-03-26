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
from json import JSONDecodeError

from aiohttp import web

from ...client import Client
from ...instance import PluginInstance
from ...loader import PluginLoader
from .base import routes
from .responses import resp


@routes.get("/instances")
async def get_instances(_: web.Request) -> web.Response:
    return resp.found([instance.to_dict() for instance in PluginInstance.cache.values()])


@routes.get("/instance/{id}")
async def get_instance(request: web.Request) -> web.Response:
    instance_id = request.match_info["id"].lower()
    instance = await PluginInstance.get(instance_id)
    if not instance:
        return resp.instance_not_found
    return resp.found(instance.to_dict())


async def _create_instance(instance_id: str, data: dict) -> web.Response:
    plugin_type = data.get("type")
    primary_user = data.get("primary_user")
    if not plugin_type:
        return resp.plugin_type_required
    elif not primary_user:
        return resp.primary_user_required
    elif not await Client.get(primary_user):
        return resp.primary_user_not_found
    try:
        PluginLoader.find(plugin_type)
    except KeyError:
        return resp.plugin_type_not_found
    instance = await PluginInstance.get(instance_id, type=plugin_type, primary_user=primary_user)
    instance.enabled = data.get("enabled", True)
    instance.config_str = data.get("config") or ""
    await instance.update()
    await instance.load()
    await instance.start()
    return resp.created(instance.to_dict())


async def _update_instance(instance: PluginInstance, data: dict) -> web.Response:
    if not await instance.update_primary_user(data.get("primary_user")):
        return resp.primary_user_not_found
    await instance.update_id(data.get("id"))
    await instance.update_enabled(data.get("enabled"))
    await instance.update_config(data.get("config"))
    await instance.update_started(data.get("started"))
    await instance.update_type(data.get("type"))
    return resp.updated(instance.to_dict())


@routes.put("/instance/{id}")
async def update_instance(request: web.Request) -> web.Response:
    instance_id = request.match_info["id"].lower()
    instance = await PluginInstance.get(instance_id)
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
    instance_id = request.match_info["id"].lower()
    instance = await PluginInstance.get(instance_id)
    if not instance:
        return resp.instance_not_found
    if instance.started:
        await instance.stop()
    await instance.delete()
    return resp.deleted

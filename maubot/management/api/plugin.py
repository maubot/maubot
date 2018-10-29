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
from aiohttp import web
from io import BytesIO
import os.path

from ...loader import PluginLoader, ZippedPluginLoader, MaubotZipImportError
from .responses import (ErrPluginNotFound, ErrPluginInUse, ErrInputPluginInvalid,
                        ErrPluginReloadFailed, RespDeleted, RespOK)
from . import routes, config


def _plugin_to_dict(plugin: PluginLoader) -> dict:
    return {
        **plugin.to_dict(),
        "instances": [instance.to_dict() for instance in plugin.references]
    }


@routes.get("/plugins")
async def get_plugins(_) -> web.Response:
    return web.json_response([_plugin_to_dict(plugin) for plugin in PluginLoader.id_cache.values()])


@routes.get("/plugin/{id}")
async def get_plugin(request: web.Request) -> web.Response:
    plugin_id = request.match_info.get("id", None)
    plugin = PluginLoader.id_cache.get(plugin_id, None)
    if not plugin:
        return ErrPluginNotFound
    return web.json_response(_plugin_to_dict(plugin))


@routes.delete("/plugin/{id}")
async def delete_plugin(request: web.Request) -> web.Response:
    plugin_id = request.match_info.get("id", None)
    plugin = PluginLoader.id_cache.get(plugin_id, None)
    if not plugin:
        return ErrPluginNotFound
    elif len(plugin.references) > 0:
        return ErrPluginInUse
    await plugin.delete()
    return RespDeleted


@routes.post("/plugin/{id}/reload")
async def reload_plugin(request: web.Request) -> web.Response:
    plugin_id = request.match_info.get("id", None)
    plugin = PluginLoader.id_cache.get(plugin_id, None)
    if not plugin:
        return ErrPluginNotFound
    return await reload(plugin)


@routes.post("/plugins/upload")
async def upload_plugin(request: web.Request) -> web.Response:
    content = await request.read()
    file = BytesIO(content)
    try:
        pid, version = ZippedPluginLoader.verify_meta(file)
    except MaubotZipImportError as e:
        return ErrInputPluginInvalid(e)
    plugin = PluginLoader.id_cache.get(pid, None)
    if not plugin:
        path = os.path.join(config["plugin_directories.upload"], f"{pid}-v{version}.mbp")
        with open(path, "wb") as p:
            p.write(content)
        try:
            ZippedPluginLoader.get(path)
        except MaubotZipImportError as e:
            ZippedPluginLoader.trash(path)
            # TODO log error?
            return ErrInputPluginInvalid(e)
    elif isinstance(plugin, ZippedPluginLoader):
        dirname = os.path.dirname(plugin.path)
        filename = os.path.basename(plugin.path)
        if plugin.version in filename:
            filename = filename.replace(plugin.version, version)
        else:
            filename = filename.rstrip(".mbp") + version + ".mbp"
        path = os.path.join(dirname, filename)
        with open(path, "wb") as p:
            p.write(content)
        ZippedPluginLoader.trash(plugin.path, reason="update")
        plugin.path = path
        return await reload(plugin)
    else:
        return web.json_response({})


async def reload(plugin: PluginLoader) -> web.Response:
    await plugin.stop_instances()
    try:
        await plugin.reload()
    except MaubotZipImportError as e:
        return ErrPluginReloadFailed(e)
    await plugin.start_instances()
    return RespOK

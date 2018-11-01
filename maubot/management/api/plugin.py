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
from time import time
import traceback
import os.path
import re

from ...loader import PluginLoader, ZippedPluginLoader, MaubotZipImportError
from .responses import (ErrPluginNotFound, ErrPluginInUse, plugin_import_error,
                        plugin_reload_error, RespDeleted, RespOK, ErrUnsupportedPluginLoader)
from .base import routes, get_config


@routes.get("/plugins")
async def get_plugins(_) -> web.Response:
    return web.json_response([plugin.to_dict() for plugin in PluginLoader.id_cache.values()])


@routes.get("/plugin/{id}")
async def get_plugin(request: web.Request) -> web.Response:
    plugin_id = request.match_info.get("id", None)
    plugin = PluginLoader.id_cache.get(plugin_id, None)
    if not plugin:
        return ErrPluginNotFound
    return web.json_response(plugin.to_dict())


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

    await plugin.stop_instances()
    try:
        await plugin.reload()
    except MaubotZipImportError as e:
        return plugin_reload_error(str(e), traceback.format_exc())
    await plugin.start_instances()
    return RespOK


async def upload_new_plugin(content: bytes, pid: str, version: str) -> web.Response:
    path = os.path.join(get_config()["plugin_directories.upload"], f"{pid}-v{version}.mbp")
    with open(path, "wb") as p:
        p.write(content)
    try:
        plugin = ZippedPluginLoader.get(path)
    except MaubotZipImportError as e:
        ZippedPluginLoader.trash(path)
        return plugin_import_error(str(e), traceback.format_exc())
    return web.json_response(plugin.to_dict())


async def upload_replacement_plugin(plugin: ZippedPluginLoader, content: bytes, new_version: str
                                    ) -> web.Response:
    dirname = os.path.dirname(plugin.path)
    old_filename = os.path.basename(plugin.path)
    if plugin.version in old_filename:
        filename = old_filename.replace(plugin.version, new_version)
        if filename == old_filename:
            filename = re.sub(f"{re.escape(plugin.version)}(-ts[0-9]+)?",
                              f"{new_version}-ts{int(time())}", old_filename)
    else:
        filename = old_filename.rstrip(".mbp")
        filename = f"{filename}-v{new_version}.mbp"
    path = os.path.join(dirname, filename)
    with open(path, "wb") as p:
        p.write(content)
    old_path = plugin.path
    await plugin.stop_instances()
    try:
        await plugin.reload(new_path=path)
    except MaubotZipImportError as e:
        try:
            await plugin.reload(new_path=old_path)
            await plugin.start_instances()
        except MaubotZipImportError:
            pass
        return plugin_import_error(str(e), traceback.format_exc())
    await plugin.start_instances()
    ZippedPluginLoader.trash(old_path, reason="update")
    return web.json_response(plugin.to_dict())


@routes.post("/plugins/upload")
async def upload_plugin(request: web.Request) -> web.Response:
    content = await request.read()
    file = BytesIO(content)
    try:
        pid, version = ZippedPluginLoader.verify_meta(file)
    except MaubotZipImportError as e:
        return plugin_import_error(str(e), traceback.format_exc())
    plugin = PluginLoader.id_cache.get(pid, None)
    if not plugin:
        return await upload_new_plugin(content, pid, version)
    elif isinstance(plugin, ZippedPluginLoader):
        return await upload_replacement_plugin(plugin, content, version)
    else:
        return ErrUnsupportedPluginLoader

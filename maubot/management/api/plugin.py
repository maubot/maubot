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
from http import HTTPStatus
from io import BytesIO
from time import time
import traceback
import os.path
import re

from aiohttp import web

from ...loader import PluginLoader, ZippedPluginLoader, MaubotZipImportError
from .responses import resp
from .base import routes, get_config


@routes.get("/plugins")
async def get_plugins(_) -> web.Response:
    return resp.found([plugin.to_dict() for plugin in PluginLoader.id_cache.values()])


@routes.get("/plugin/{id}")
async def get_plugin(request: web.Request) -> web.Response:
    plugin_id = request.match_info.get("id", None)
    plugin = PluginLoader.id_cache.get(plugin_id, None)
    if not plugin:
        return resp.plugin_not_found
    return resp.found(plugin.to_dict())


@routes.delete("/plugin/{id}")
async def delete_plugin(request: web.Request) -> web.Response:
    plugin_id = request.match_info.get("id", None)
    plugin = PluginLoader.id_cache.get(plugin_id, None)
    if not plugin:
        return resp.plugin_not_found
    elif len(plugin.references) > 0:
        return resp.plugin_in_use
    await plugin.delete()
    return resp.deleted


@routes.post("/plugin/{id}/reload")
async def reload_plugin(request: web.Request) -> web.Response:
    plugin_id = request.match_info.get("id", None)
    plugin = PluginLoader.id_cache.get(plugin_id, None)
    if not plugin:
        return resp.plugin_not_found

    await plugin.stop_instances()
    try:
        await plugin.reload()
    except MaubotZipImportError as e:
        return resp.plugin_reload_error(str(e), traceback.format_exc())
    await plugin.start_instances()
    return resp.ok


@routes.put("/plugin/{id}")
async def put_plugin(request: web.Request) -> web.Response:
    plugin_id = request.match_info.get("id", None)
    content = await request.read()
    file = BytesIO(content)
    try:
        pid, version = ZippedPluginLoader.verify_meta(file)
    except MaubotZipImportError as e:
        return resp.plugin_import_error(str(e), traceback.format_exc())
    if pid != plugin_id:
        return resp.pid_mismatch
    plugin = PluginLoader.id_cache.get(plugin_id, None)
    if not plugin:
        return await upload_new_plugin(content, pid, version)
    elif isinstance(plugin, ZippedPluginLoader):
        return await upload_replacement_plugin(plugin, content, version)
    else:
        return resp.unsupported_plugin_loader


@routes.post("/plugins/upload")
async def upload_plugin(request: web.Request) -> web.Response:
    content = await request.read()
    file = BytesIO(content)
    try:
        pid, version = ZippedPluginLoader.verify_meta(file)
    except MaubotZipImportError as e:
        return resp.plugin_import_error(str(e), traceback.format_exc())
    plugin = PluginLoader.id_cache.get(pid, None)
    if not plugin:
        return await upload_new_plugin(content, pid, version)
    elif not request.query.get("allow_override"):
        return resp.plugin_exists
    elif isinstance(plugin, ZippedPluginLoader):
        return await upload_replacement_plugin(plugin, content, version)
    else:
        return resp.unsupported_plugin_loader


async def upload_new_plugin(content: bytes, pid: str, version: str) -> web.Response:
    path = os.path.join(get_config()["plugin_directories.upload"], f"{pid}-v{version}.mbp")
    with open(path, "wb") as p:
        p.write(content)
    try:
        plugin = ZippedPluginLoader.get(path)
    except MaubotZipImportError as e:
        ZippedPluginLoader.trash(path)
        return resp.plugin_import_error(str(e), traceback.format_exc())
    return resp.created(plugin.to_dict())


async def upload_replacement_plugin(plugin: ZippedPluginLoader, content: bytes, new_version: str
                                    ) -> web.Response:
    dirname = os.path.dirname(plugin.path)
    old_filename = os.path.basename(plugin.path)
    if plugin.version in old_filename:
        replacement = (new_version if plugin.version != new_version
                       else f"{new_version}-ts{int(time())}")
        filename = re.sub(f"{re.escape(plugin.version)}(-ts[0-9]+)?",
                          replacement, old_filename)
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
        return resp.plugin_import_error(str(e), traceback.format_exc())
    await plugin.start_instances()
    ZippedPluginLoader.trash(old_path, reason="update")
    return resp.updated(plugin.to_dict())

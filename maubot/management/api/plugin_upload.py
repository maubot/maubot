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
from io import BytesIO
from time import time
import logging
import os.path
import re
import traceback

from aiohttp import web
from packaging.version import Version

from ...loader import MaubotZipImportError, PluginLoader, ZippedPluginLoader
from .base import get_config, routes
from .responses import resp

log = logging.getLogger("maubot.server.upload")


@routes.put("/plugin/{id}")
async def put_plugin(request: web.Request) -> web.Response:
    plugin_id = request.match_info["id"]
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


async def upload_new_plugin(content: bytes, pid: str, version: Version) -> web.Response:
    path = os.path.join(get_config()["plugin_directories.upload"], f"{pid}-v{version}.mbp")
    with open(path, "wb") as p:
        p.write(content)
    try:
        plugin = ZippedPluginLoader.get(path)
    except MaubotZipImportError as e:
        ZippedPluginLoader.trash(path)
        return resp.plugin_import_error(str(e), traceback.format_exc())
    return resp.created(plugin.to_dict())


async def upload_replacement_plugin(
    plugin: ZippedPluginLoader, content: bytes, new_version: Version
) -> web.Response:
    dirname = os.path.dirname(plugin.path)
    old_filename = os.path.basename(plugin.path)
    if str(plugin.meta.version) in old_filename:
        replacement = (
            str(new_version)
            if plugin.meta.version != new_version
            else f"{new_version}-ts{int(time() * 1000)}"
        )
        filename = re.sub(
            f"{re.escape(str(plugin.meta.version))}(-ts[0-9]+)?", replacement, old_filename
        )
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
        log.exception(f"Error loading updated version of {plugin.meta.id}, rolling back")
        try:
            await plugin.reload(new_path=old_path)
            await plugin.start_instances()
        except MaubotZipImportError:
            log.warning(f"Failed to roll back update of {plugin.meta.id}", exc_info=True)
        finally:
            ZippedPluginLoader.trash(path, reason="failed_update")
        return resp.plugin_import_error(str(e), traceback.format_exc())
    try:
        await plugin.start_instances()
    except Exception as e:
        log.exception(f"Error starting {plugin.meta.id} instances after update, rolling back")
        try:
            await plugin.stop_instances()
            await plugin.reload(new_path=old_path)
            await plugin.start_instances()
        except Exception:
            log.warning(f"Failed to roll back update of {plugin.meta.id}", exc_info=True)
        finally:
            ZippedPluginLoader.trash(path, reason="failed_update")
        return resp.plugin_reload_error(str(e), traceback.format_exc())

    log.debug(f"Successfully updated {plugin.meta.id}, moving old version to trash")
    ZippedPluginLoader.trash(old_path, reason="update")
    return resp.updated(plugin.to_dict())

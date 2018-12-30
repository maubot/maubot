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
import traceback

from aiohttp import web

from ...loader import PluginLoader, MaubotZipImportError
from .responses import resp
from .base import routes


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

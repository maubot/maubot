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
from typing import Dict, List, TypeVar, Type
from zipfile import ZipFile, BadZipFile
import logging
import sys
import os
import io
import configparser

from mautrix.types import UserID

from .lib.zipimport import zipimporter, ZipImportError
from .db import DBPlugin
from .plugin_base import Plugin

log = logging.getLogger("maubot.plugin")
PluginClass = TypeVar("PluginClass", bound=Plugin)

class MaubotImportError(Exception):
    pass


class ZippedModule:
    path_cache: Dict[str, 'ZippedModule'] = {}
    id_cache: Dict[str, 'ZippedModule'] = {}

    path: str
    id: str
    version: str
    modules: List[str]
    main_class: str
    main_module: str
    loaded: bool
    _importer: zipimporter

    def __init__(self, path: str) -> None:
        self.path = path
        self.id = None
        self.loaded = False
        self._load_meta()
        self._run_preload_checks(self._get_importer())
        self.path_cache[self.path] = self
        self.id_cache[self.id] = self

    def __repr__(self) -> str:
        return ("<maubot.plugin.ZippedModule "
                f"path='{self.path}' "
                f"id='{self.id}' "
                f"loaded={self.loaded}>")

    def _load_meta(self) -> None:
        try:
            file = ZipFile(self.path)
            data = file.read("maubot.ini")
        except FileNotFoundError as e:
            raise MaubotImportError(f"Maubot plugin not found at {self.path}") from e
        except BadZipFile as e:
            raise MaubotImportError(f"File at {self.path} is not a maubot plugin") from e
        except KeyError as e:
            raise MaubotImportError(
                "File at {path} does not contain a maubot plugin definition") from e
        config = configparser.ConfigParser()
        try:
            config.read_string(data.decode("utf-8"), source=f"{self.path}/maubot.ini")
            meta = config["maubot"]
            meta_id = meta["ID"]
            version = meta["Version"]
            modules = [mod.strip() for mod in meta["Modules"].split(",")]
            main_class = meta["MainClass"]
            main_module = modules[-1]
            if "/" in main_class:
                main_module, main_class = main_class.split("/")[:2]
        except (configparser.Error, KeyError, IndexError, ValueError) as e:
            raise MaubotImportError(
                f"Maubot plugin definition in file at {self.path} is invalid") from e
        if self.id and meta_id != self.id:
            raise MaubotImportError("Maubot plugin ID changed during reload")
        self.id, self.version, self.modules = meta_id, version, modules
        self.main_class, self.main_module = main_class, main_module

    def _get_importer(self, reset_cache: bool = False) -> zipimporter:
        try:
            importer = zipimporter(self.path)
            if reset_cache:
                importer.reset_cache()
            return importer
        except ZipImportError as e:
            raise MaubotImportError(f"File at {self.path} not found or not a maubot plugin") from e

    def _run_preload_checks(self, importer: zipimporter) -> None:
        try:
            code = importer.get_code(self.main_module.replace(".", "/"))
            if self.main_class not in code.co_names:
                raise MaubotImportError(f"Main class {self.main_class} not in {self.main_module}")
        except ZipImportError as e:
            raise MaubotImportError(
                f"Main module {self.main_module} not found in {self.path}") from e
        for module in self.modules:
            try:
                importer.find_module(module)
            except ZipImportError as e:
                raise MaubotImportError(f"Module {module} not found in {self.path}") from e

    def load(self) -> Type[PluginClass]:
        importer = self._get_importer(reset_cache=self.loaded)
        self._run_preload_checks(importer)
        for module in self.modules:
            importer.load_module(module)
        self.loaded = True
        main_mod = sys.modules[self.main_module]
        plugin = getattr(main_mod, self.main_class)
        if not issubclass(plugin, Plugin):
            raise MaubotImportError(
                f"Main class of plugin at {self.path} does not extend maubot.Plugin")
        return plugin

    def reload(self) -> Type[PluginClass]:
        self.unload()
        return self.load()

    def unload(self) -> None:
        for name, mod in list(sys.modules.items()):
            if getattr(mod, "__file__", "").startswith(self.path):
                del sys.modules[name]

    def destroy(self) -> None:
        self.unload()
        try:
            del self.path_cache[self.path]
        except KeyError:
            pass
        try:
            del self.id_cache[self.id]
        except KeyError:
            pass


class PluginInstance:
    cache: Dict[str, 'PluginInstance'] = {}
    plugin_directories: List[str] = []

    def __init__(self, db_instance: DBPlugin):
        self.db_instance = db_instance
        self.cache[self.id] = self

    @property
    def id(self) -> str:
        return self.db_instance.id

    @id.setter
    def id(self, value: str) -> None:
        self.db_instance.id = value

    @property
    def type(self) -> str:
        return self.db_instance.type

    @type.setter
    def type(self, value: str) -> None:
        self.db_instance.type = value

    @property
    def enabled(self) -> bool:
        return self.db_instance.enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self.db_instance.enabled = value

    @property
    def primary_user(self) -> UserID:
        return self.db_instance.primary_user

    @primary_user.setter
    def primary_user(self, value: UserID) -> None:
        self.db_instance.primary_user = value

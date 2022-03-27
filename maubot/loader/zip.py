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

from time import time
from zipfile import BadZipFile, ZipFile
import logging
import os
import sys

from packaging.version import Version
from ruamel.yaml import YAML, YAMLError

from mautrix.types import SerializerError

from ..__meta__ import __version__
from ..config import Config
from ..lib.zipimport import ZipImportError, zipimporter
from ..plugin_base import Plugin
from .abc import IDConflictError, PluginClass, PluginLoader
from .meta import PluginMeta

current_version = Version(__version__)
yaml = YAML()


class MaubotZipImportError(Exception):
    pass


class MaubotZipMetaError(MaubotZipImportError):
    pass


class MaubotZipPreLoadError(MaubotZipImportError):
    pass


class MaubotZipLoadError(MaubotZipImportError):
    pass


class ZippedPluginLoader(PluginLoader):
    path_cache: dict[str, ZippedPluginLoader] = {}
    log: logging.Logger = logging.getLogger("maubot.loader.zip")
    trash_path: str = "delete"
    directories: list[str] = []

    path: str | None
    meta: PluginMeta | None
    main_class: str | None
    main_module: str | None
    _loaded: type[PluginClass] | None
    _importer: zipimporter | None
    _file: ZipFile | None

    def __init__(self, path: str) -> None:
        super().__init__()
        self.path = path
        self.meta = None
        self.main_class = None
        self.main_module = None
        self._loaded = None
        self._importer = None
        self._file = None
        self._load_meta()
        self._run_preload_checks(self._get_importer())
        try:
            existing = self.id_cache[self.meta.id]
            raise IDConflictError(
                f"Plugin with id {self.meta.id} already loaded from {existing.source}"
            )
        except KeyError:
            pass
        self.path_cache[self.path] = self
        self.id_cache[self.meta.id] = self
        self.log.debug(f"Preloaded plugin {self.meta.id} from {self.path}")

    def to_dict(self) -> dict:
        return {**super().to_dict(), "path": self.path}

    @classmethod
    def get(cls, path: str) -> ZippedPluginLoader:
        path = os.path.abspath(path)
        try:
            return cls.path_cache[path]
        except KeyError:
            return cls(path)

    @property
    def source(self) -> str:
        return self.path

    def __repr__(self) -> str:
        return (
            "<ZippedPlugin "
            f"path='{self.path}' "
            f"meta={self.meta} "
            f"loaded={self._loaded is not None}>"
        )

    def sync_read_file(self, path: str) -> bytes:
        return self._file.read(path)

    async def read_file(self, path: str) -> bytes:
        return self.sync_read_file(path)

    def sync_list_files(self, directory: str) -> list[str]:
        directory = directory.rstrip("/")
        return [
            file.filename
            for file in self._file.filelist
            if os.path.dirname(file.filename) == directory
        ]

    async def list_files(self, directory: str) -> list[str]:
        return self.sync_list_files(directory)

    @staticmethod
    def _read_meta(source) -> tuple[ZipFile, PluginMeta]:
        try:
            file = ZipFile(source)
            data = file.read("maubot.yaml")
        except FileNotFoundError as e:
            raise MaubotZipMetaError("Maubot plugin not found") from e
        except BadZipFile as e:
            raise MaubotZipMetaError("File is not a maubot plugin") from e
        except KeyError as e:
            raise MaubotZipMetaError("File does not contain a maubot plugin definition") from e
        try:
            meta_dict = yaml.load(data)
        except (YAMLError, KeyError, IndexError, ValueError) as e:
            raise MaubotZipMetaError("Maubot plugin definition file is not valid YAML") from e
        try:
            meta = PluginMeta.deserialize(meta_dict)
        except SerializerError as e:
            raise MaubotZipMetaError("Maubot plugin definition in file is invalid") from e
        if meta.maubot > current_version:
            raise MaubotZipMetaError(
                f"Plugin requires maubot {meta.maubot}, but this instance is {current_version}"
            )
        return file, meta

    @classmethod
    def verify_meta(cls, source) -> tuple[str, Version]:
        _, meta = cls._read_meta(source)
        return meta.id, meta.version

    def _load_meta(self) -> None:
        file, meta = self._read_meta(self.path)
        if self.meta and meta.id != self.meta.id:
            raise MaubotZipMetaError("Maubot plugin ID changed during reload")
        self.meta = meta
        if "/" in meta.main_class:
            self.main_module, self.main_class = meta.main_class.split("/")[:2]
        else:
            self.main_module = meta.modules[0]
            self.main_class = meta.main_class
        self._file = file

    def _get_importer(self, reset_cache: bool = False) -> zipimporter:
        try:
            if not self._importer or self._importer.archive != self.path:
                self._importer = zipimporter(self.path)
            if reset_cache:
                self._importer.reset_cache()
            return self._importer
        except ZipImportError as e:
            raise MaubotZipMetaError("File not found or not a maubot plugin") from e

    def _run_preload_checks(self, importer: zipimporter) -> None:
        try:
            code = importer.get_code(self.main_module.replace(".", "/"))
            if self.main_class not in code.co_names:
                raise MaubotZipPreLoadError(
                    f"Main class {self.main_class} not in {self.main_module}"
                )
        except ZipImportError as e:
            raise MaubotZipPreLoadError(f"Main module {self.main_module} not found in file") from e
        for module in self.meta.modules:
            try:
                importer.find_module(module)
            except ZipImportError as e:
                raise MaubotZipPreLoadError(f"Module {module} not found in file") from e

    async def load(self, reset_cache: bool = False) -> type[PluginClass]:
        try:
            return self._load(reset_cache)
        except MaubotZipImportError:
            self.log.exception(f"Failed to load {self.meta.id} v{self.meta.version}")
            raise

    def _load(self, reset_cache: bool = False) -> type[PluginClass]:
        if self._loaded is not None and not reset_cache:
            return self._loaded
        self._load_meta()
        importer = self._get_importer(reset_cache=reset_cache)
        self._run_preload_checks(importer)
        if reset_cache:
            self.log.debug(f"Re-preloaded plugin {self.meta.id} from {self.path}")
        for module in self.meta.modules:
            try:
                importer.load_module(module)
            except ZipImportError:
                raise MaubotZipLoadError(f"Module {module} not found in file")
            except Exception:
                raise MaubotZipLoadError(f"Failed to load module {module}")
        try:
            main_mod = sys.modules[self.main_module]
        except KeyError as e:
            raise MaubotZipLoadError(f"Main module {self.main_module} of plugin not found") from e
        try:
            plugin = getattr(main_mod, self.main_class)
        except AttributeError as e:
            raise MaubotZipLoadError(f"Main class {self.main_class} of plugin not found") from e
        if not issubclass(plugin, Plugin):
            raise MaubotZipLoadError("Main class of plugin does not extend maubot.Plugin")
        self._loaded = plugin
        self.log.debug(f"Loaded and imported plugin {self.meta.id} from {self.path}")
        return plugin

    async def reload(self, new_path: str | None = None) -> type[PluginClass]:
        self._unload()
        if new_path is not None and new_path != self.path:
            try:
                del self.path_cache[self.path]
            except KeyError:
                pass
            self.path = new_path
            self.path_cache[self.path] = self
        return await self.load(reset_cache=True)

    def _unload(self) -> None:
        for name, mod in list(sys.modules.items()):
            if (getattr(mod, "__file__", "") or "").startswith(self.path):
                del sys.modules[name]
        self._loaded = None
        self.log.debug(f"Unloaded plugin {self.meta.id} at {self.path}")

    async def delete(self) -> None:
        self._unload()
        try:
            del self.path_cache[self.path]
        except KeyError:
            pass
        try:
            del self.id_cache[self.meta.id]
        except KeyError:
            pass
        if self._importer:
            self._importer.remove_cache()
            self._importer = None
        self._loaded = None
        self.trash(self.path, reason="delete")
        self.meta = None
        self.path = None

    @classmethod
    def trash(cls, file_path: str, new_name: str | None = None, reason: str = "error") -> None:
        if cls.trash_path == "delete":
            try:
                os.remove(file_path)
            except FileNotFoundError:
                pass
        else:
            new_name = new_name or f"{int(time())}-{reason}-{os.path.basename(file_path)}"
            try:
                os.rename(file_path, os.path.abspath(os.path.join(cls.trash_path, new_name)))
            except OSError as e:
                cls.log.warning(f"Failed to rename {file_path}: {e} - trying to delete")
                try:
                    os.remove(file_path)
                except FileNotFoundError:
                    pass

    @classmethod
    def load_all(cls):
        cls.log.debug("Preloading plugins...")
        for directory in cls.directories:
            for file in os.listdir(directory):
                if not file.endswith(".mbp"):
                    continue
                path = os.path.abspath(os.path.join(directory, file))
                try:
                    cls.get(path)
                except MaubotZipImportError:
                    cls.log.exception(f"Failed to load plugin at {path}, trashing...")
                    cls.trash(path)
                except IDConflictError:
                    cls.log.error(f"Duplicate plugin ID at {path}, trashing...")
                    cls.trash(path)


def init(config: Config) -> None:
    ZippedPluginLoader.trash_path = config["plugin_directories.trash"]
    ZippedPluginLoader.directories = config["plugin_directories.load"]
    ZippedPluginLoader.load_all()

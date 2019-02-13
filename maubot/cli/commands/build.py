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
from typing import Optional, Union, IO
from io import BytesIO
import zipfile
import os

from mautrix.client.api.types.util import SerializerError
from ruamel.yaml import YAML, YAMLError
from colorama import Fore
from PyInquirer import prompt
import click

from ...loader import PluginMeta
from ..cliq.validators import PathValidator
from ..base import app
from ..config import get_default_server, get_token
from .upload import upload_file

yaml = YAML()


def zipdir(zip, dir):
    for root, dirs, files in os.walk(dir):
        for file in files:
            zip.write(os.path.join(root, file))


def read_meta(path: str) -> Optional[PluginMeta]:
    try:
        with open(os.path.join(path, "maubot.yaml")) as meta_file:
            try:
                meta_dict = yaml.load(meta_file)
            except YAMLError as e:
                print(Fore.RED + "Failed to build plugin: Metadata file is not YAML")
                print(Fore.RED + str(e) + Fore.RESET)
                return None
    except FileNotFoundError:
        print(Fore.RED + "Failed to build plugin: Metadata file not found" + Fore.RESET)
        return None
    try:
        meta = PluginMeta.deserialize(meta_dict)
    except SerializerError as e:
        print(Fore.RED + "Failed to build plugin: Metadata file is not valid")
        print(Fore.RED + str(e) + Fore.RESET)
        return None
    return meta


def read_output_path(output: str, meta: PluginMeta) -> Optional[str]:
    directory = os.getcwd()
    filename = f"{meta.id}-v{meta.version}.mbp"
    if not output:
        output = os.path.join(directory, filename)
    elif os.path.isdir(output):
        output = os.path.join(output, filename)
    elif os.path.exists(output):
        override = prompt({
            "type": "confirm",
            "name": "override",
            "message": f"{output} exists, override?"
        })["override"]
        if not override:
            return None
        os.remove(output)
    return os.path.abspath(output)


def write_plugin(meta: PluginMeta, output: Union[str, IO]) -> None:
    with zipfile.ZipFile(output, "w") as zip:
        meta_dump = BytesIO()
        yaml.dump(meta.serialize(), meta_dump)
        zip.writestr("maubot.yaml", meta_dump.getvalue())

        for module in meta.modules:
            if os.path.isfile(f"{module}.py"):
                zip.write(f"{module}.py")
            elif module is not None and os.path.isdir(module):
                zipdir(zip, module)
            else:
                print(Fore.YELLOW + f"Module {module} not found, skipping" + Fore.RESET)

        for file in meta.extra_files:
            zip.write(file)


def upload_plugin(output: Union[str, IO], server: str) -> None:
    if not server:
        server, token = get_default_server()
    else:
        token = get_token(server)
    if not token:
        return
    if isinstance(output, str):
        with open(output, "rb") as file:
            upload_file(file, server, token)
    else:
        upload_file(output, server, token)


@app.command(short_help="Build a maubot plugin",
             help="Build a maubot plugin. First parameter is the path to root of the plugin "
                  "to build. You can also use --output to specify output file.")
@click.argument("path", default=os.getcwd())
@click.option("-o", "--output", help="Path to output built plugin to",
              type=PathValidator.click_type)
@click.option("-u", "--upload", help="Upload plugin to server after building", is_flag=True,
              default=False)
@click.option("-s", "--server", help="Server to upload built plugin to")
def build(path: str, output: str, upload: bool, server: str) -> None:
    meta = read_meta(path)
    if not meta:
        return
    if output or not upload:
        output = read_output_path(output, meta)
        if not output:
            return
    else:
        output = BytesIO()
    os.chdir(path)
    write_plugin(meta, output)
    if isinstance(output, str):
        print(f"{Fore.GREEN}Plugin built to {Fore.CYAN}{output}{Fore.GREEN}.{Fore.RESET}")
    else:
        output.seek(0)
    if upload:
        upload_plugin(output, server)

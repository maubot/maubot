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
from pkg_resources import resource_string
import os

from packaging.version import Version
from jinja2 import Template

from .. import cliq
from ..cliq import SPDXValidator, VersionValidator
from ..util import spdx

loaded: bool = False
meta_template: Template
mod_template: Template
base_config: str


def load_templates():
    global mod_template, meta_template, base_config, loaded
    if loaded:
        return
    meta_template = Template(resource_string("maubot.cli", "res/maubot.yaml.j2").decode("utf-8"))
    mod_template = Template(resource_string("maubot.cli", "res/plugin.py.j2").decode("utf-8"))
    base_config = resource_string("maubot.cli", "res/config.yaml").decode("utf-8")
    loaded = True


@cliq.command(help="Initialize a new maubot plugin")
@cliq.option("-n", "--name", help="The name of the project", required=True,
             default=os.path.basename(os.getcwd()))
@cliq.option("-i", "--id", message="ID", required=True,
             help="The maubot plugin ID (Java package name format)")
@cliq.option("-v", "--version", help="Initial version for project (PEP-440 format)",
             default="0.1.0", validator=VersionValidator, required=True)
@cliq.option("-l", "--license", validator=SPDXValidator, default="AGPL-3.0-or-later",
             help="The license for the project (SPDX identifier)", required=False)
@cliq.option("-c", "--config", message="Should the plugin include a config?",
             help="Include a config in the plugin stub", default=False, is_flag=True)
def init(name: str, id: str, version: Version, license: str, config: bool) -> None:
    load_templates()
    main_class = name[0].upper() + name[1:]
    meta = meta_template.render(id=id, version=str(version), license=license, config=config,
                                main_class=main_class)
    with open("maubot.yaml", "w") as file:
        file.write(meta)
    if license:
        with open("LICENSE", "w") as file:
            file.write(spdx.get(license)["text"])
    if not os.path.isdir(name):
        os.mkdir(name)
    mod = mod_template.render(config=config, name=main_class)
    with open(f"{name}/__init__.py", "w") as file:
        file.write(mod)
    if config:
        with open("base-config.yaml", "w") as file:
            file.write(base_config)

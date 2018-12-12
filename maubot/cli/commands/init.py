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
import click
import os

from ..base import app
from ..util import type_path


@app.command(help="Initialize a new maubot plugin")
@click.option("-n", "--name", help="The name of the project", default=os.path.basename(os.getcwd()),
              prompt=True, show_default="directory name")
@click.option("-i", "--id", help="The maubot plugin ID (Java package name format)", prompt=True)
@click.option("-v", "--version", help="Initial version for project", default="0.1.0",
              show_default=True)
@click.option("-l", "--license", help="The SPDX license identifier of the license for the project",
              prompt=True, default="AGPL-3.0-or-later")
@click.option("-c", "--config", help="Include a config in the plugin stub", is_flag=True,
              default=False)
def init(name: str, id: str, version: str, license: str, config: bool) -> None:
    pass

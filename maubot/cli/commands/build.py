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


@app.command(short_help="Build a maubot plugin",
             help="Build a maubot plugin. First parameter is the path to root of the plugin "
                  "to build. You can also use --output to specify output file.")
@click.argument("path", default=".")
@click.option("-o", "--output", help="Path to output built plugin to", type=type_path)
@click.option("-u", "--upload", help="Upload plugin to main server after building", is_flag=True,
              default=False)
def build(path: str, output: str, upload: bool) -> None:
    pass

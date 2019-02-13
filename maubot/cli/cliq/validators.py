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
from typing import Callable
import os

from packaging.version import Version, InvalidVersion
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.document import Document
import click

from ..util import spdx as spdxlib


class Required(Validator):
    proxy: Validator

    def __init__(self, proxy: Validator = None) -> None:
        self.proxy = proxy

    def validate(self, document: Document) -> None:
        if len(document.text) == 0:
            raise ValidationError(message="This field is required")
        if self.proxy:
            return self.proxy.validate(document)


class ClickValidator(Validator):
    click_type: Callable[[str], str] = None

    @classmethod
    def validate(cls, document: Document) -> None:
        try:
            cls.click_type(document.text)
        except click.BadParameter as e:
            raise ValidationError(message=e.message, cursor_position=len(document.text))


def path(val: str) -> str:
    val = os.path.abspath(val)
    if os.path.exists(val):
        return val
    directory = os.path.dirname(val)
    if not os.path.isdir(directory):
        if os.path.exists(directory):
            raise click.BadParameter(f"{directory} is not a directory")
        raise click.BadParameter(f"{directory} does not exist")
    return val


class PathValidator(ClickValidator):
    click_type = path


def version(val: str) -> Version:
    try:
        return Version(val)
    except InvalidVersion as e:
        raise click.BadParameter(f"{val} is not a valid PEP-440 version") from e


class VersionValidator(ClickValidator):
    click_type = version


def spdx(val: str) -> str:
    if not spdxlib.valid(val):
        raise click.BadParameter(f"{val} is not a valid SPDX license identifier")
    return val


class SPDXValidator(ClickValidator):
    click_type = spdx

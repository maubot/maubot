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
from typing import Any, Callable, Union, Optional
import functools

from prompt_toolkit.validation import Validator
from PyInquirer import prompt
import click

from ..base import app
from .validators import Required, ClickValidator


def command(help: str) -> Callable[[Callable], Callable]:
    def decorator(func) -> Callable:
        questions = func.__inquirer_questions__.copy()

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for key, value in kwargs.items():
                if value is not None and (questions[key]["type"] != "confirm" or value != "null"):
                    questions.pop(key, None)
            question_list = list(questions.values())
            question_list.reverse()
            resp = prompt(question_list, keyboard_interrupt_msg="Aborted!")
            if not resp and question_list:
                return
            kwargs = {**kwargs, **resp}
            func(*args, **kwargs)

        return app.command(help=help)(wrapper)

    return decorator


def yesno(val: str) -> Optional[bool]:
    if not val:
        return None
    elif val.lower() in ("true", "t", "yes", "y"):
        return True
    elif val.lower() in ("false", "f", "no", "n"):
        return False


yesno.__name__ = "yes/no"


def option(short: str, long: str, message: str = None, help: str = None,
           click_type: Union[str, Callable[[str], Any]] = None, inq_type: str = None,
           validator: Validator = None, required: bool = False, default: str = None,
           is_flag: bool = False) -> Callable[[Callable], Callable]:
    if not message:
        message = long[2].upper() + long[3:]
    click_type = validator.click_type if isinstance(validator, ClickValidator) else click_type
    if is_flag:
        click_type = yesno

    def decorator(func) -> Callable:
        click.option(short, long, help=help, type=click_type)(func)
        if not hasattr(func, "__inquirer_questions__"):
            func.__inquirer_questions__ = {}
        q = {
            "type": (inq_type if isinstance(inq_type, str)
                     else ("input" if not is_flag
                           else "confirm")),
            "name": long[2:],
            "message": message,
        }
        if default is not None:
            q["default"] = default
        if required:
            q["validator"] = Required(validator)
        elif validator:
            q["validator"] = validator
        func.__inquirer_questions__[long[2:]] = q
        return func

    return decorator

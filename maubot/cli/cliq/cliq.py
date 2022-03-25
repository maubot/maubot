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

from typing import Any, Callable
import asyncio
import functools
import inspect
import traceback

from colorama import Fore
from prompt_toolkit.validation import Validator
from questionary import prompt
import aiohttp
import click

from ..base import app
from ..config import get_token
from .validators import ClickValidator, Required


def with_http(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        async with aiohttp.ClientSession() as sess:
            try:
                return await func(*args, sess=sess, **kwargs)
            except aiohttp.ClientError as e:
                print(f"{Fore.RED}Connection error: {e}{Fore.RESET}")

    return wrapper


def with_authenticated_http(func):
    @functools.wraps(func)
    async def wrapper(*args, server: str, **kwargs):
        server, token = get_token(server)
        if not token:
            return
        async with aiohttp.ClientSession(headers={"Authorization": f"Bearer {token}"}) as sess:
            try:
                return await func(*args, sess=sess, server=server, **kwargs)
            except aiohttp.ClientError as e:
                print(f"{Fore.RED}Connection error: {e}{Fore.RESET}")

    return wrapper


def command(help: str) -> Callable[[Callable], Callable]:
    def decorator(func) -> Callable:
        questions = getattr(func, "__inquirer_questions__", {}).copy()

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for key, value in kwargs.items():
                if key not in questions:
                    continue
                if value is not None and (questions[key]["type"] != "confirm" or value != "null"):
                    questions.pop(key, None)
                try:
                    required_unless = questions[key].pop("required_unless")
                    if isinstance(required_unless, str) and kwargs[required_unless]:
                        questions.pop(key)
                    elif isinstance(required_unless, list):
                        for v in required_unless:
                            if kwargs[v]:
                                questions.pop(key)
                                break
                    elif isinstance(required_unless, dict):
                        for k, v in required_unless.items():
                            if kwargs.get(v, object()) == v:
                                questions.pop(key)
                                break
                except KeyError:
                    pass
            question_list = list(questions.values())
            question_list.reverse()
            resp = prompt(question_list, kbi_msg="Aborted!")
            if not resp and question_list:
                return
            kwargs = {**kwargs, **resp}

            try:
                res = func(*args, **kwargs)
                if inspect.isawaitable(res):
                    asyncio.run(res)
            except Exception:
                print(Fore.RED + "Fatal error running command" + Fore.RESET)
                traceback.print_exc()

        return app.command(help=help)(wrapper)

    return decorator


def yesno(val: str) -> bool | None:
    if not val:
        return None
    elif isinstance(val, bool):
        return val
    elif val.lower() in ("true", "t", "yes", "y"):
        return True
    elif val.lower() in ("false", "f", "no", "n"):
        return False


yesno.__name__ = "yes/no"


def option(
    short: str,
    long: str,
    message: str = None,
    help: str = None,
    click_type: str | Callable[[str], Any] = None,
    inq_type: str = None,
    validator: type[Validator] = None,
    required: bool = False,
    default: str | bool | None = None,
    is_flag: bool = False,
    prompt: bool = True,
    required_unless: str | list | dict = None,
) -> Callable[[Callable], Callable]:
    if not message:
        message = long[2].upper() + long[3:]

    if isinstance(validator, type) and issubclass(validator, ClickValidator):
        click_type = validator.click_type
    if is_flag:
        click_type = yesno

    def decorator(func) -> Callable:
        click.option(short, long, help=help, type=click_type)(func)
        if not prompt:
            return func
        if not hasattr(func, "__inquirer_questions__"):
            func.__inquirer_questions__ = {}
        q = {
            "type": (
                inq_type if isinstance(inq_type, str) else ("input" if not is_flag else "confirm")
            ),
            "name": long[2:],
            "message": message,
        }
        if required_unless is not None:
            q["required_unless"] = required_unless
        if default is not None:
            q["default"] = default
        if required or required_unless is not None:
            q["validate"] = Required(validator)
        elif validator:
            q["validate"] = validator
        func.__inquirer_questions__[long[2:]] = q
        return func

    return decorator

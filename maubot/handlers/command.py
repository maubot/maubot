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
from typing import Union, Callable, Sequence, Pattern, Awaitable, NewType, Optional, Any
import functools
import re

from mautrix.client import EventHandler
from mautrix.types import MessageType

from ..matrix import MaubotMessageEvent
from .event import EventHandlerDecorator

PrefixType = Union[str, Callable[[], str]]
CommandDecorator = Callable[[PrefixType, str], EventHandlerDecorator]


def _get_subcommand_decorator(parent: EventHandler) -> CommandDecorator:
    def subcommand(name: PrefixType, help: str = None) -> EventHandlerDecorator:
        cmd_decorator = new(name=f"{parent.__mb_name__} {name}", help=help)

        def decorator(func: EventHandler) -> EventHandler:
            func = cmd_decorator(func)
            parent.__mb_subcommands__.append(func)
            return func

        return decorator

    return subcommand


def new(name: Union[str, Callable[[], str]], help: str = None) -> EventHandlerDecorator:
    def decorator(func: EventHandler) -> EventHandler:
        func.__mb_subcommands__ = []
        func.__mb_help__ = help
        func.__mb_name__ = name or func.__name__
        func.subcommand = _get_subcommand_decorator(func)
        return func

    return decorator


PassiveCommandHandler = Callable[[MaubotMessageEvent, ...], Awaitable[None]]
PassiveCommandHandlerDecorator = NewType("PassiveCommandHandlerDecorator",
                                         Callable[[PassiveCommandHandler], PassiveCommandHandler])


def passive(regex: Union[str, Pattern], msgtypes: Sequence[MessageType] = (MessageType.TEXT,),
            field: Callable[[MaubotMessageEvent], str] = lambda event: event.content.body
            ) -> PassiveCommandHandlerDecorator:
    if not isinstance(regex, Pattern):
        regex = re.compile(regex)

    def decorator(func: PassiveCommandHandler) -> PassiveCommandHandler:
        @functools.wraps(func)
        async def replacement(event: MaubotMessageEvent) -> None:
            if event.sender == event.client.mxid:
                return
            elif msgtypes and event.content.msgtype not in msgtypes:
                return
            match = regex.match(field(event))
            if match:
                await func(event, *list(match.groups()))

        return replacement

    return decorator


class _Argument:
    def __init__(self, name: str, required: bool, matches: Optional[str],
                 parser: Optional[Callable[[str], Any]]) -> None:
        pass


def argument(name: str, *, required: bool = True, matches: Optional[str] = None,
             parser: Optional[Callable[[str], Any]] = None) -> EventHandlerDecorator:
    def decorator(func: EventHandler) -> EventHandler:
        if not hasattr(func, "__mb_arguments__"):
            func.__mb_arguments__ = []
        func.__mb_arguments__.append(_Argument(name, required, matches, parser))
        return func

    return decorator


def vararg(func: EventHandler) -> EventHandler:
    func.__mb_vararg__ = True
    return func

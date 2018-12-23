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
from typing import Union, Callable, Sequence, Pattern, Awaitable, NewType, Optional, Any, List, Dict
import functools
import re

from mautrix.types import MessageType, EventType

from ..matrix import MaubotMessageEvent
from . import event

PrefixType = Optional[Union[str, Callable[[], str]]]
CommandHandlerFunc = NewType("CommandHandlerFunc",
                             Callable[[MaubotMessageEvent, Any], Awaitable[Any]])
CommandHandlerDecorator = NewType("CommandHandlerDecorator",
                                  Callable[[Union['CommandHandler', CommandHandlerFunc]],
                                           'CommandHandler'])
PassiveCommandHandlerDecorator = NewType("PassiveCommandHandlerDecorator",
                                         Callable[[CommandHandlerFunc], CommandHandlerFunc])


class CommandHandler:
    def __init__(self, func: CommandHandlerFunc) -> None:
        self.__mb_func__: CommandHandlerFunc = func
        self.__mb_subcommands__: Dict[str, CommandHandler] = {}
        self.__mb_arguments__: List[Argument] = []
        self.__mb_help__: str = None
        self.__mb_name__: str = None
        self.__mb_prefix__: str = None
        self.__mb_require_subcommand__: bool = True
        self.__mb_event_handler__: bool = True
        self.__mb_event_type__: EventType = EventType.ROOM_MESSAGE
        self.__class_instance: Any = None

    async def __call__(self, evt: MaubotMessageEvent, *,
                       _existing_args: Dict[str, Any] = None) -> Any:
        body = evt.content.body
        if evt.sender == evt.client.mxid or not body.startswith(self.__mb_prefix__):
            return
        call_args: Dict[str, Any] = {**_existing_args} if _existing_args else {}
        remaining_val = body[len(self.__mb_prefix__) + 1:]
        # TODO update remaining_val somehow
        for arg in self.__mb_arguments__:
            try:
                call_args[arg.name] = arg.match(remaining_val)
                if arg.required and not call_args[arg.name]:
                    raise ValueError("Argument required")
            except ArgumentSyntaxError as e:
                await evt.reply(e.message + (f"\n{self.__mb_usage__}" if e.show_usage else ""))
                return
            except ValueError as e:
                await evt.reply(self.__mb_usage__)
                return

        if len(self.__mb_subcommands__) > 0:
            split = remaining_val.split(" ") if len(remaining_val) > 0 else []
            try:
                subcommand = self.__mb_subcommands__[split[0]]
                return await subcommand(evt, _existing_args=call_args)
            except (KeyError, IndexError):
                if self.__mb_require_subcommand__:
                    await evt.reply(self.__mb_full_help__)
                    return
        return (await self.__mb_func__(self.__class_instance, evt, **call_args)
                if self.__class_instance
                else await self.__mb_func__(evt, **call_args))

    def __get__(self, instance, instancetype):
        self.__class_instance = instance
        return self

    @property
    def __mb_full_help__(self) -> str:
        basic = self.__mb_usage__
        usage = f"{basic} <subcommand> [...]\n\n"
        usage += "\n".join(f"* {cmd.__mb_name__} {cmd.__mb_usage_args__} - {cmd.__mb_help__}"
                           for cmd in self.__mb_subcommands__.values())
        return usage

    @property
    def __mb_usage_args__(self) -> str:
        return " ".join(f"<{arg.label}>" if arg.required else f"[{arg.label}]"
                        for arg in self.__mb_arguments__)

    @property
    def __mb_usage__(self) -> str:
        return f"**Usage:** {self.__mb_prefix__} {self.__mb_usage_args__}"

    def subcommand(self, name: PrefixType = None, help: str = None
                   ) -> CommandHandlerDecorator:
        def decorator(func: Union[CommandHandler, CommandHandlerFunc]) -> CommandHandler:
            if not isinstance(func, CommandHandler):
                func = CommandHandler(func)
            func.__mb_name__ = name or func.__name__
            func.__mb_prefix__ = f"{self.__mb_prefix__} {func.__mb_name__}"
            func.__mb_help__ = help
            func.__mb_event_handler__ = False
            self.__mb_subcommands__[func.__mb_name__] = func
            return func

        return decorator


class ArgumentSyntaxError(ValueError):
    def __init__(self, message: str, show_usage: bool = True) -> None:
        super().__init__(message)
        self.message = message
        self.show_usage = show_usage


class Argument:
    def __init__(self, name: str, label: str = None, *, required: bool = False,
                 matches: Optional[str] = None, parser: Optional[Callable[[str], Any]] = None,
                 pass_raw: bool = False) -> None:
        self.name = name
        self.required = required
        self.label = label or name

        if not parser:
            if matches:
                regex = re.compile(matches)

                def parser(val: str) -> Optional[Sequence[str]]:
                    match = regex.match(val)
                    return match.groups() if match else None
            else:
                def parser(val: str) -> str:
                    return val

        if not pass_raw:
            o_parser = parser

            def parser(val: str) -> Any:
                val = val.strip().split(" ")
                return o_parser(val[0])

        self.parser = parser

    def match(self, val: str) -> Any:
        return self.parser(val)

    def __call__(self, func: Union[CommandHandler, CommandHandlerFunc]) -> CommandHandler:
        if not isinstance(func, CommandHandler):
            func = CommandHandler(func)
        func.__mb_arguments__.append(self)
        return func


def new(name: PrefixType, *, help: str = None, event_type: EventType = EventType.ROOM_MESSAGE,
        require_subcommand: bool = True) -> CommandHandlerDecorator:
    def decorator(func: Union[CommandHandler, CommandHandlerFunc]) -> CommandHandler:
        if not isinstance(func, CommandHandler):
            func = CommandHandler(func)
        func.__mb_help__ = help
        func.__mb_name__ = name or func.__name__
        func.__mb_require_subcommand__ = require_subcommand
        func.__mb_prefix__ = f"!{func.__mb_name__}"
        func.__mb_event_type__ = event_type
        return func

    return decorator


def argument(name: str, label: str = None, *, required: bool = True, matches: Optional[str] = None,
             parser: Optional[Callable[[str], Any]] = None) -> CommandHandlerDecorator:
    return Argument(name, label, required=required, matches=matches, parser=parser)


def passive(regex: Union[str, Pattern], msgtypes: Sequence[MessageType] = (MessageType.TEXT,),
            field: Callable[[MaubotMessageEvent], str] = lambda event: event.content.body,
            event_type: EventType = EventType.ROOM_MESSAGE) -> PassiveCommandHandlerDecorator:
    if not isinstance(regex, Pattern):
        regex = re.compile(regex)

    def decorator(func: CommandHandlerFunc) -> CommandHandlerFunc:
        @event.on(event_type)
        @functools.wraps(func)
        async def replacement(self, evt: MaubotMessageEvent) -> None:
            if isinstance(self, MaubotMessageEvent):
                evt = self
                self = None
            if evt.sender == evt.client.mxid:
                return
            elif msgtypes and evt.content.msgtype not in msgtypes:
                return
            match = regex.match(field(evt))
            if match:
                if self:
                    await func(self, evt, *list(match.groups()))
                else:
                    await func(evt, *list(match.groups()))

        return replacement

    return decorator

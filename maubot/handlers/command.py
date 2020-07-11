# maubot - A plugin-based Matrix bot system.
# Copyright (C) 2019 Tulir Asokan
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
from typing import (Union, Callable, Sequence, Pattern, Awaitable, NewType, Optional, Any, List,
                    Dict, Tuple, Set, Iterable)
from abc import ABC, abstractmethod
import asyncio
import functools
import inspect
import re

from mautrix.types import MessageType, EventType

from ..matrix import MaubotMessageEvent
from . import event

PrefixType = Optional[Union[str, Callable[[], str]]]
AliasesType = Union[List[str], Tuple[str, ...], Set[str], Callable[[str], bool]]
CommandHandlerFunc = NewType("CommandHandlerFunc",
                             Callable[[MaubotMessageEvent, Any], Awaitable[Any]])
CommandHandlerDecorator = NewType("CommandHandlerDecorator",
                                  Callable[[Union['CommandHandler', CommandHandlerFunc]],
                                           'CommandHandler'])
PassiveCommandHandlerDecorator = NewType("PassiveCommandHandlerDecorator",
                                         Callable[[CommandHandlerFunc], CommandHandlerFunc])


def _split_in_two(val: str, split_by: str) -> List[str]:
    return val.split(split_by, 1) if split_by in val else [val, ""]


class CommandHandler:
    def __init__(self, func: CommandHandlerFunc) -> None:
        self.__mb_func__: CommandHandlerFunc = func
        self.__mb_parent__: Optional[CommandHandler] = None
        self.__mb_subcommands__: List[CommandHandler] = []
        self.__mb_arguments__: List[Argument] = []
        self.__mb_help__: Optional[str] = None
        self.__mb_get_name__: Callable[[Any], str] = lambda s: "noname"
        self.__mb_is_command_match__: Callable[[Any, str], bool] = self.__command_match_unset
        self.__mb_require_subcommand__: bool = True
        self.__mb_arg_fallthrough__: bool = True
        self.__mb_event_handler__: bool = True
        self.__mb_event_type__: EventType = EventType.ROOM_MESSAGE
        self.__mb_msgtypes__: Iterable[MessageType] = (MessageType.TEXT,)
        self.__bound_copies__: Dict[Any, CommandHandler] = {}
        self.__bound_instance__: Any = None

    def __get__(self, instance, instancetype):
        if not instance or self.__bound_instance__:
            return self
        try:
            return self.__bound_copies__[instance]
        except KeyError:
            new_ch = type(self)(self.__mb_func__)
            keys = ["parent", "subcommands", "arguments", "help", "get_name", "is_command_match",
                    "require_subcommand", "arg_fallthrough", "event_handler", "event_type",
                    "msgtypes"]
            for key in keys:
                key = f"__mb_{key}__"
                setattr(new_ch, key, getattr(self, key))
            new_ch.__bound_instance__ = instance
            new_ch.__mb_subcommands__ = [subcmd.__get__(instance, instancetype)
                                         for subcmd in self.__mb_subcommands__]
            self.__bound_copies__[instance] = new_ch
            return new_ch

    @staticmethod
    def __command_match_unset(self, val: str) -> bool:
        raise NotImplementedError("Hmm")

    async def __call__(self, evt: MaubotMessageEvent, *, _existing_args: Dict[str, Any] = None,
                       remaining_val: str = None) -> Any:
        if evt.sender == evt.client.mxid or evt.content.msgtype not in self.__mb_msgtypes__:
            return
        if remaining_val is None:
            if not evt.content.body or evt.content.body[0] != "!":
                return
            command, remaining_val = _split_in_two(evt.content.body[1:], " ")
            command = command.lower()
            if not self.__mb_is_command_match__(self.__bound_instance__, command):
                return
        call_args: Dict[str, Any] = {**_existing_args} if _existing_args else {}

        if not self.__mb_arg_fallthrough__ and len(self.__mb_subcommands__) > 0:
            ok, res = await self.__call_subcommand__(evt, call_args, remaining_val)
            if ok:
                return res

        ok, remaining_val = await self.__parse_args__(evt, call_args, remaining_val)
        if not ok:
            return
        elif self.__mb_arg_fallthrough__ and len(self.__mb_subcommands__) > 0:
            ok, res = await self.__call_subcommand__(evt, call_args, remaining_val)
            if ok:
                return res
            elif self.__mb_require_subcommand__:
                await evt.reply(self.__mb_full_help__)
                return

        if self.__bound_instance__:
            return await self.__mb_func__(self.__bound_instance__, evt, **call_args)
        return await self.__mb_func__(evt, **call_args)

    async def __call_subcommand__(self, evt: MaubotMessageEvent, call_args: Dict[str, Any],
                                  remaining_val: str) -> Tuple[bool, Any]:
        command, remaining_val = _split_in_two(remaining_val.strip(), " ")
        for subcommand in self.__mb_subcommands__:
            if subcommand.__mb_is_command_match__(subcommand.__bound_instance__, command):
                return True, await subcommand(evt, _existing_args=call_args,
                                              remaining_val=remaining_val)
        return False, None

    async def __parse_args__(self, evt: MaubotMessageEvent, call_args: Dict[str, Any],
                             remaining_val: str) -> Tuple[bool, str]:
        for arg in self.__mb_arguments__:
            try:
                remaining_val, call_args[arg.name] = arg.match(remaining_val.strip(), evt=evt,
                                                               instance=self.__bound_instance__)
                if arg.required and call_args[arg.name] is None:
                    raise ValueError("Argument required")
            except ArgumentSyntaxError as e:
                await evt.reply(e.message + (f"\n{self.__mb_usage__}" if e.show_usage else ""))
                return False, remaining_val
            except ValueError:
                await evt.reply(self.__mb_usage__)
                return False, remaining_val
        return True, remaining_val

    @property
    def __mb_full_help__(self) -> str:
        usage = self.__mb_usage_without_subcommands__ + "\n\n"
        usage += "\n".join(cmd.__mb_usage_inline__ for cmd in self.__mb_subcommands__)
        return usage

    @property
    def __mb_usage_args__(self) -> str:
        arg_usage = " ".join(f"<{arg.label}>" if arg.required else f"[{arg.label}]"
                             for arg in self.__mb_arguments__)
        if self.__mb_subcommands__ and self.__mb_arg_fallthrough__:
            arg_usage += " " + self.__mb_usage_subcommand__
        return arg_usage

    @property
    def __mb_usage_subcommand__(self) -> str:
        return f"<subcommand> [...]"

    @property
    def __mb_name__(self) -> str:
        return self.__mb_get_name__(self.__bound_instance__)

    @property
    def __mb_prefix__(self) -> str:
        if self.__mb_parent__:
            return (f"!{self.__mb_parent__.__mb_get_name__(self.__bound_instance__)} "
                    f"{self.__mb_name__}")
        return f"!{self.__mb_name__}"

    @property
    def __mb_usage_inline__(self) -> str:
        if not self.__mb_arg_fallthrough__:
            return (f"* {self.__mb_name__} {self.__mb_usage_args__} - {self.__mb_help__}\n"
                    f"* {self.__mb_name__} {self.__mb_usage_subcommand__}")
        return f"* {self.__mb_name__} {self.__mb_usage_args__} - {self.__mb_help__}"

    @property
    def __mb_subcommands_list__(self) -> str:
        return f"**Subcommands:** {', '.join(sc.__mb_name__ for sc in self.__mb_subcommands__)}"

    @property
    def __mb_usage_without_subcommands__(self) -> str:
        if not self.__mb_arg_fallthrough__:
            return (f"**Usage:** {self.__mb_prefix__} {self.__mb_usage_args__}"
                    f" _OR_ {self.__mb_usage_subcommand__}")
        return f"**Usage:** {self.__mb_prefix__} {self.__mb_usage_args__}"

    @property
    def __mb_usage__(self) -> str:
        if len(self.__mb_subcommands__) > 0:
            return f"{self.__mb_usage_without_subcommands__}  \n{self.__mb_subcommands_list__}"
        return self.__mb_usage_without_subcommands__

    def subcommand(self, name: PrefixType = None, *, help: str = None, aliases: AliasesType = None,
                   required_subcommand: bool = True, arg_fallthrough: bool = True,
                   ) -> CommandHandlerDecorator:
        def decorator(func: Union[CommandHandler, CommandHandlerFunc]) -> CommandHandler:
            if not isinstance(func, CommandHandler):
                func = CommandHandler(func)
            new(name, help=help, aliases=aliases, require_subcommand=required_subcommand,
                arg_fallthrough=arg_fallthrough)(func)
            func.__mb_parent__ = self
            func.__mb_event_handler__ = False
            self.__mb_subcommands__.append(func)
            return func

        return decorator


def new(name: PrefixType = None, *, help: str = None, aliases: AliasesType = None,
        event_type: EventType = EventType.ROOM_MESSAGE, msgtypes: Iterable[MessageType] = None,
        require_subcommand: bool = True, arg_fallthrough: bool = True) -> CommandHandlerDecorator:
    def decorator(func: Union[CommandHandler, CommandHandlerFunc]) -> CommandHandler:
        if not isinstance(func, CommandHandler):
            func = CommandHandler(func)
        func.__mb_help__ = help
        if name:
            if callable(name):
                if len(inspect.getfullargspec(name).args) == 0:
                    func.__mb_get_name__ = lambda self: name()
                else:
                    func.__mb_get_name__ = name
            else:
                func.__mb_get_name__ = lambda self: name
        else:
            func.__mb_get_name__ = lambda self: func.__name__
        if callable(aliases):
            if len(inspect.getfullargspec(aliases).args) == 1:
                func.__mb_is_command_match__ = lambda self, val: aliases(val)
            else:
                func.__mb_is_command_match__ = aliases
        elif isinstance(aliases, (list, set, tuple)):
            func.__mb_is_command_match__ = lambda self, val: (val == func.__mb_get_name__(self)
                                                              or val in aliases)
        else:
            func.__mb_is_command_match__ = lambda self, val: val == func.__mb_get_name__(self)
        # Decorators are executed last to first, so we reverse the argument list.
        func.__mb_arguments__.reverse()
        func.__mb_require_subcommand__ = require_subcommand
        func.__mb_arg_fallthrough__ = arg_fallthrough
        func.__mb_event_type__ = event_type
        if msgtypes:
            func.__mb_msgtypes__ = msgtypes
        return func

    return decorator


class ArgumentSyntaxError(ValueError):
    def __init__(self, message: str, show_usage: bool = True) -> None:
        super().__init__(message)
        self.message = message
        self.show_usage = show_usage


class Argument(ABC):
    def __init__(self, name: str, label: str = None, *, required: bool = False,
                 pass_raw: bool = False) -> None:
        self.name = name
        self.label = label or name
        self.required = required
        self.pass_raw = pass_raw

    @abstractmethod
    def match(self, val: str, **kwargs) -> Tuple[str, Any]:
        pass

    def __call__(self, func: Union[CommandHandler, CommandHandlerFunc]) -> CommandHandler:
        if not isinstance(func, CommandHandler):
            func = CommandHandler(func)
        func.__mb_arguments__.append(self)
        return func


class RegexArgument(Argument):
    def __init__(self, name: str, label: str = None, *, required: bool = False,
                 pass_raw: bool = False, matches: str = None) -> None:
        super().__init__(name, label, required=required, pass_raw=pass_raw)
        matches = f"^{matches}" if self.pass_raw else f"^{matches}$"
        self.regex = re.compile(matches)

    def match(self, val: str, **kwargs) -> Tuple[str, Any]:
        orig_val = val
        if not self.pass_raw:
            val = re.split(r"\s", val, 1)[0]
        match = self.regex.match(val)
        if match:
            return (orig_val[:match.start()] + orig_val[match.end():],
                    match.groups() or val[match.start():match.end()])
        return orig_val, None


class CustomArgument(Argument):
    def __init__(self, name: str, label: str = None, *, required: bool = False,
                 pass_raw: bool = False, matcher: Callable[[str], Any]) -> None:
        super().__init__(name, label, required=required, pass_raw=pass_raw)
        self.matcher = matcher

    def match(self, val: str, **kwargs) -> Tuple[str, Any]:
        if self.pass_raw:
            return self.matcher(val)
        orig_val = val
        val = re.split(r"\s", val, 1)[0]
        res = self.matcher(val)
        if res is not None:
            return orig_val[len(val):], res
        return orig_val, None


class SimpleArgument(Argument):
    def match(self, val: str, **kwargs) -> Tuple[str, Any]:
        if self.pass_raw:
            return "", val
        res = re.split(r"\s", val, 1)[0]
        return val[len(res):], res


def argument(name: str, label: str = None, *, required: bool = True, matches: Optional[str] = None,
             parser: Optional[Callable[[str], Any]] = None, pass_raw: bool = False
             ) -> CommandHandlerDecorator:
    if matches:
        return RegexArgument(name, label, required=required, matches=matches, pass_raw=pass_raw)
    elif parser:
        return CustomArgument(name, label, required=required, matcher=parser, pass_raw=pass_raw)
    else:
        return SimpleArgument(name, label, required=required, pass_raw=pass_raw)


def passive(regex: Union[str, Pattern], *, msgtypes: Sequence[MessageType] = (MessageType.TEXT,),
            field: Callable[[MaubotMessageEvent], str] = lambda evt: evt.content.body,
            event_type: EventType = EventType.ROOM_MESSAGE, multiple: bool = False,
            case_insensitive: bool = False, multiline: bool = False, dot_all: bool = False
            ) -> PassiveCommandHandlerDecorator:
    if not isinstance(regex, Pattern):
        flags = re.RegexFlag.UNICODE
        if case_insensitive:
            flags |= re.IGNORECASE
        if multiline:
            flags |= re.MULTILINE
        if dot_all:
            flags |= re.DOTALL
        regex = re.compile(regex, flags=flags)

    def decorator(func: CommandHandlerFunc) -> CommandHandlerFunc:
        combine = None
        if hasattr(func, "__mb_passive_orig__"):
            combine = func
            func = func.__mb_passive_orig__

        @event.on(event_type)
        @functools.wraps(func)
        async def replacement(self, evt: MaubotMessageEvent = None) -> None:
            if not evt and isinstance(self, MaubotMessageEvent):
                evt = self
                self = None
            if evt.sender == evt.client.mxid:
                return
            elif msgtypes and evt.content.msgtype not in msgtypes:
                return
            data = field(evt)
            if multiple:
                val = [(data[match.pos:match.endpos], *match.groups())
                       for match in regex.finditer(data)]
            else:
                match = regex.search(data)
                if match:
                    val = (data[match.pos:match.endpos], *match.groups())
                else:
                    val = None
            if val:
                if self:
                    await func(self, evt, val)
                else:
                    await func(evt, val)

        if combine:
            orig_replacement = replacement

            @event.on(event_type)
            @functools.wraps(func)
            async def replacement(self, evt: MaubotMessageEvent = None) -> None:
                await asyncio.gather(combine(self, evt), orig_replacement(self, evt))

        replacement.__mb_passive_orig__ = func

        return replacement

    return decorator

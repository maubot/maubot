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
from typing import Callable, Union, NewType, Any, Tuple, Optional
import functools
import re

from mautrix.types import EventType, Event, EventContent, MessageEvent, MessageEventContent
from mautrix.client import EventHandler

EventHandlerDecorator = NewType("EventHandlerDecorator", Callable[[EventHandler], EventHandler])


def handler(var: Union[EventType, EventHandler]) -> Union[EventHandlerDecorator, EventHandler]:
    def decorator(func: EventHandler) -> EventHandler:
        func.__mb_event_handler__ = True
        if isinstance(var, EventType):
            func.__mb_event_type__ = var
        else:
            func.__mb_event_type__ = EventType.ALL

        return func

    if isinstance(var, EventType):
        return decorator
    else:
        decorator(var)


class Field:
    body: Callable[[MessageEventContent], str] = lambda content: content.body
    msgtype: Callable[[MessageEventContent], str] = lambda content: content.msgtype


def _parse_key(key: str) -> Tuple[str, Optional[str]]:
    if '.' not in key:
        return key, None
    key, next_key = key.split('.', 1)
    if len(key) > 0 and key[0] == "[":
        end_index = next_key.index("]")
        key = key[1:] + "." + next_key[:end_index]
        next_key = next_key[end_index + 2:] if len(next_key) > end_index + 1 else None
    return key, next_key


def _recursive_get(data: EventContent, key: str) -> Any:
    key, next_key = _parse_key(key)
    if next_key is not None:
        next_data = data.get(key, None)
        if next_data is None:
            return None
        return _recursive_get(next_data, next_key)
    return data.get(key, None)


def _find_content_field(content: EventContent, field: str) -> Any:
    val = _recursive_get(content, field)
    if not val and hasattr(content, "unrecognized_"):
        val = _recursive_get(content.unrecognized_, field)
    return val


def handle_own_events(func: EventHandler) -> EventHandler:
    func.__mb_handle_own_events__ = True


def filter_content(field: Union[str, Callable[[EventContent], Any]], substr: str = None,
                   pattern: str = None, exact: bool = False):
    if substr and pattern:
        raise ValueError("You can only provide one of substr or pattern.")
    elif not substr and not pattern:
        raise ValueError("You must provide either substr or pattern.")

    if not callable(field):
        field = functools.partial(_find_content_field, field=field)

    if substr:
        def func(evt: MessageEvent) -> bool:
            val = field(evt.content)
            if val is None:
                return False
            elif substr in val:
                return True
    else:
        pattern = re.compile(pattern)

        def func(evt: MessageEvent) -> bool:
            val = field(evt.content)
            if val is None:
                return False
            elif pattern.match(val):
                return True

    return filter(func)


def filter(func: Callable[[MessageEvent], bool]) -> EventHandlerDecorator:
    def decorator(func: EventHandler) -> EventHandler:
        if not hasattr(func, "__mb_event_filters__"):
            func.__mb_event_filters__ = []
        func.__mb_event_filters__.append(func)
        return func

    return decorator

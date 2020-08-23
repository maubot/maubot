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
from typing import Callable, Union, NewType

from mautrix.types import EventType
from mautrix.client import EventHandler, InternalEventType

EventHandlerDecorator = NewType("EventHandlerDecorator", Callable[[EventHandler], EventHandler])


def on(var: Union[EventType, InternalEventType, EventHandler]
       ) -> Union[EventHandlerDecorator, EventHandler]:
    def decorator(func: EventHandler) -> EventHandler:
        func.__mb_event_handler__ = True
        if isinstance(var, (EventType, InternalEventType)):
            func.__mb_event_type__ = var
        else:
            func.__mb_event_type__ = EventType.ALL

        return func

    return decorator if isinstance(var, (EventType, InternalEventType)) else decorator(var)


def off(func: EventHandler) -> EventHandler:
    func.__mb_event_handler__ = False
    return func

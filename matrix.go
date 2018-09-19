// maubot - A plugin-based Matrix bot system written in Go.
// Copyright (C) 2018 Tulir Asokan
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

package maubot

import (
	"maunium.net/go/gomatrix"
)

type EventHandler func(*Event) EventHandlerResult
type EventHandlerResult int
type CommandHandlerResult = EventHandlerResult

const (
	Continue EventHandlerResult = iota
	StopEventPropagation
	StopCommandPropagation CommandHandlerResult = iota
)

type MatrixClient interface {
	AddEventHandler(gomatrix.EventType, EventHandler)
	AddCommandHandler(string, CommandHandler)
	SetCommandSpec(*CommandSpec)
	GetEvent(string, string) *Event
}

type EventFuncs interface {
	MarkRead() error
	Reply(string) (string, error)
	ReplyContent(gomatrix.Content) (string, error)
	SendMessage(string) (string, error)
	SendContent(gomatrix.Content) (string, error)
	SendRawEvent(gomatrix.EventType, interface{}) (string, error)
}

type Event struct {
	EventFuncs
	*gomatrix.Event
}

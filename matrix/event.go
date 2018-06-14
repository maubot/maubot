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

package matrix

import (
	"maubot.xyz/interfaces"
	"maunium.net/go/gomatrix"
)

type Event struct {
	*gomatrix.Event
	Client *Client
}

func (evt *Event) Interface() *interfaces.Event {
	var stateKey string
	if evt.StateKey != nil {
		stateKey = *evt.StateKey
	}
	return &interfaces.Event{
		EventFuncs: evt,
		StateKey:   stateKey,
		Sender:     evt.Sender,
		Type:       evt.Type,
		Timestamp:  evt.Timestamp,
		ID:         evt.ID,
		RoomID:     evt.RoomID,
		Content:    evt.Content,
		Redacts:    evt.Redacts,
		Unsigned: interfaces.Unsigned{
			PrevContent:   evt.Unsigned.PrevContent,
			PrevSender:    evt.Unsigned.PrevSender,
			ReplacesState: evt.Unsigned.ReplacesState,
			Age:           evt.Unsigned.Age,
		},
	}
}

func (evt *Event) Reply(text string) (string, error) {
	return evt.SendEvent(
		SetReply(
			RenderMarkdown(text),
			evt.Event))
}

func (evt *Event) SendMessage(text string) (string, error) {
	return evt.SendEvent(RenderMarkdown(text))
}

func (evt *Event) SendEvent(content map[string]interface{}) (string, error) {
	resp, err := evt.Client.SendMessageEvent(evt.RoomID, "m.room.message", content)
	if err != nil {
		return "", err
	}
	return resp.EventID, nil
}

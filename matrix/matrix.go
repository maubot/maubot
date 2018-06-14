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
	"maubot.xyz/database"
	"maubot.xyz/interfaces"
	"maunium.net/go/gomatrix"
	log "maunium.net/go/maulogger"
)

type Client struct {
	*gomatrix.Client

	DB *database.MatrixClient
}

func NewClient(db *database.MatrixClient) (*Client, error) {
	mxClient, err := gomatrix.NewClient(db.Homeserver, db.UserID, db.AccessToken)
	if err != nil {
		return nil, err
	}

	client := &Client{
		Client: mxClient,
		DB:     db,
	}

	client.Syncer = NewMaubotSyncer(client, client.Store)

	client.AddEventHandler(gomatrix.StateMember, client.onJoin)

	return client, nil
}

func (client *Client) ParseEvent(evt *gomatrix.Event) *Event {
	return &Event{
		Client: client,
		Event: evt,
	}
}

func (client *Client) AddEventHandler(evt string, handler interfaces.EventHandler) {
	client.Syncer.(*MaubotSyncer).OnEventType(evt, handler)
}

func (client *Client) onJoin(evt *interfaces.Event) bool {
	if !client.DB.AutoJoinRooms || evt.StateKey != client.DB.UserID {
		return true
	}
	if membership, _ := evt.Content["membership"].(string); membership == "invite" {
		client.JoinRoom(evt.RoomID)
		return false
	}
	return true
}

func (client *Client) JoinRoom(roomID string) {
	client.Client.JoinRoom(roomID, "", nil)
}

func (client *Client) Sync() {
	go func() {
		err := client.Client.Sync()
		if err != nil {
			log.Errorln("Sync() in client", client.UserID, "errored:", err)
		}
	}()
}

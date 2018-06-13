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

	client.AddEventHandler(gomatrix.StateMember, client.onJoin)

	return client, nil
}

func (client *Client) AddEventHandler(evt string, handler gomatrix.OnEventListener) {
	client.Syncer.(*gomatrix.DefaultSyncer).OnEventType(evt, handler)
}

func (client *Client) onJoin(evt *gomatrix.Event) {
	if !client.DB.AutoJoinRooms || evt.StateKey == nil || *evt.StateKey != client.DB.UserID {
		return
	}
	if membership, _ := evt.Content["membership"].(string); membership == "invite" {
		client.JoinRoom(evt.RoomID)
	}
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

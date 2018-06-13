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
	"os"

	"maubot.xyz/matrix"
	log "maunium.net/go/maulogger"
)

func (bot *Bot) initClients() {
	log.Debugln("Initializing Matrix clients")
	clients := bot.Database.MatrixClient.GetAll()
	for _, client := range clients {
		mxClient, err := matrix.NewClient(client)
		if err != nil {
			log.Fatalf("Failed to create client to %s as %s: %v\n", client.Homeserver, client.UserID, err)
			os.Exit(3)
		}
		log.Debugln("Initialized user", client.UserID, "with homeserver", client.Homeserver)
		bot.Clients[client.UserID] = mxClient
	}
}

func (bot *Bot) startClients() {
	log.Debugln("Starting Matrix syncer")
	for _, client := range bot.Clients {
		if client.DB.Sync {
			client.Sync()
		}
	}
}

func (bot *Bot) stopClients() {
	log.Debugln("Stopping Matrix syncers")
	for _, client := range bot.Clients {
		client.StopSync()
	}
}

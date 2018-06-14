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

package app

import (
	"net/http"
	"os"

	"maubot.xyz"
	"maubot.xyz/config"
	"maubot.xyz/database"
	"maubot.xyz/matrix"
	log "maunium.net/go/maulogger"
)

type Bot struct {
	Config         *config.MainConfig
	Database       *database.Database
	Clients        map[string]*matrix.Client
	PluginCreators map[string]*maubot.PluginCreator
	Plugins        map[string]*PluginWrapper
	Server         *http.Server
}

func New(config *config.MainConfig) *Bot {
	return &Bot{
		Config:         config,
		Clients:        make(map[string]*matrix.Client),
		Plugins:        make(map[string]*PluginWrapper),
		PluginCreators: make(map[string]*maubot.PluginCreator),
	}
}

func (bot *Bot) Init() {
	bot.initDatabase()
	bot.initClients()
	bot.initServer()
	bot.loadPlugins()
	bot.createPlugins()
	log.Debugln("Init func exit")
}

func (bot *Bot) Start() {
	go bot.startClients()
	go bot.startServer()
	bot.startPlugins()
	log.Debugln("Start func exit")
}

func (bot *Bot) Stop() {
	bot.stopPlugins()
	bot.stopServer()
	bot.stopClients()
	log.Debugln("Stop func exit")
}

func (bot *Bot) initDatabase() {
	log.Debugln("Initializing database")
	bot.Database = &bot.Config.Database
	err := bot.Database.Connect()
	if err != nil {
		log.Fatalln("Failed to connect to database:", err)
		os.Exit(2)
	}
	bot.Database.CreateTables()
}

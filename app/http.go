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
	"context"
	"net/http"
	"os"
	"time"

	"github.com/gorilla/mux"
	log "maunium.net/go/maulogger"
)

func (bot *Bot) initServer() {
	log.Debugln("Initializing HTTP server")
	r := mux.NewRouter()
	http.Handle(bot.Config.Server.BasePath, r)
	bot.Server = &http.Server{
		Addr:         bot.Config.Server.Listen,
		WriteTimeout: time.Second * 15,
		ReadTimeout:  time.Second * 15,
		IdleTimeout:  time.Second * 60,
		Handler:      r,
	}
}

func (bot *Bot) startServer() {
	log.Debugf("Listening at http://%s%s\n", bot.Server.Addr, bot.Config.Server.BasePath)
	if err := bot.Server.ListenAndServe(); err != nil {
		log.Fatalln("HTTP server errored:", err)
		bot.Server = nil
		bot.Stop()
		os.Exit(10)
	}
}

func (bot *Bot) stopServer() {
	if bot.Server != nil {
		log.Debugln("Stopping HTTP server")
		ctx, cancel := context.WithTimeout(context.Background(), time.Second*5)
		defer cancel()
		bot.Server.Shutdown(ctx)
	}
}

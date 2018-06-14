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

package main

import (
	"fmt"
	"os"
	"os/signal"
	"syscall"

	_ "github.com/mattn/go-sqlite3"
	"maubot.xyz/app"
	"maubot.xyz/config"
	flag "maunium.net/go/mauflag"
	log "maunium.net/go/maulogger"
)

func main() {
	flag.SetHelpTitles("maubot - A plugin-based Matrix bot system written in Go.", "maubot [-c /path/to/config] [-h]")
	configPath := flag.MakeFull("c", "config", "The path to the main config file", "maubot.yaml").String()
	wantHelp, _ := flag.MakeHelpFlag()

	err := flag.Parse()
	if err != nil {
		fmt.Println(err)
		flag.PrintHelp()
		os.Exit(1)
	}

	if *wantHelp {
		flag.PrintHelp()
		return
	}

	cfg := &config.MainConfig{}
	err = cfg.Load(*configPath)
	if err != nil {
		fmt.Println("Failed to load config:", err)
		return
	}
	cfg.Logging.Configure(log.DefaultLogger)
	log.Debugln("Logger configured")

	bot := app.New(cfg)
	bot.Init()
	bot.Start()

	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt, syscall.SIGTERM)
	<-c
	log.Debugln("Interrupt received, stopping components...")
	bot.Stop()
	log.Debugln("Components stopped, bye!")
	os.Exit(0)
}

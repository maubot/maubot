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
	"io/ioutil"
	"os"
	"path/filepath"

	log "maunium.net/go/maulogger"
)

func (bot *Bot) loadPlugin(dir, fileName string) {
	ext := fileName[len(fileName)-4:]
	if ext != ".mbp" {
		return
	}

	path := filepath.Join(dir, fileName)

	pluginCreator, err := LoadPlugin(path)
	if err != nil {
		log.Fatalf("Failed to load plugin at %s: %v\n", path, err)
		os.Exit(4)
	}

	_, exists := bot.PluginCreators[pluginCreator.Name]
	if exists {
		log.Debugf("Skipping plugin at %s: plugin with same name already loaded", path)
		return
	}

	bot.PluginCreators[pluginCreator.Name] = pluginCreator
	log.Debugf("Loaded plugin creator %s v%s\n", pluginCreator.Name, pluginCreator.Version)
}

func (bot *Bot) loadPlugins() {
	for _, dir := range bot.Config.PluginDirs {
		files, err := ioutil.ReadDir(dir)
		if err != nil {
			log.Fatalf("Failed to read plugin directory %s: %v\n", dir, err)
			os.Exit(4)
		}
		for _, file := range files {
			bot.loadPlugin(dir, file.Name())
		}
	}
}

func (bot *Bot) createPlugins() {
	log.Debugln("Creating plugin instances")
	plugins := bot.Database.Plugin.GetAll()
	for _, plugin := range plugins {
		if !plugin.Enabled {
			log.Debugln("Skipping disabled plugin", plugin.ID)
			continue
		}

		creator, ok := bot.PluginCreators[plugin.Type]
		if !ok {
			log.Errorln("Plugin creator", plugin.Type, "for", plugin.ID, "not found, disabling plugin...")
			plugin.Enabled = false
			plugin.Update()
			continue
		}

		client, ok := bot.Clients[plugin.UserID]
		if !ok {
			log.Errorln("Client", plugin.UserID, "for", plugin.ID, "not found, disabling plugin...")
			plugin.Enabled = false
			plugin.Update()
			continue
		}


		log.Debugf("Created plugin %s (type %s v%s)\n", plugin.ID, creator.Name, creator.Version)
		bot.Plugins[plugin.ID] = &PluginWrapper{
			Plugin:  creator.Create(bot, plugin, client),
			Creator: creator,
			DB:      plugin,
		}
	}
}

func (bot *Bot) startPlugins() {
	log.Debugln("Starting plugin instances...")
	for _, plugin := range bot.Plugins {
		log.Debugf("Starting plugin %s (type %s v%s)\n", plugin.DB.ID, plugin.Creator.Name, plugin.Creator.Version)
		go plugin.Start()
	}
}

func (bot *Bot) stopPlugins() {
	log.Debugln("Stopping plugin instances...")
	for _, plugin := range bot.Plugins {
		log.Debugf("Stopping plugin %s (type %s v%s)\n", plugin.DB.ID, plugin.Creator.Name, plugin.Creator.Version)
		plugin.Stop()
	}
}

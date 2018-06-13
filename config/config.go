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

package config

import (
	"io/ioutil"

	"gopkg.in/yaml.v2"
	"maubot.xyz/database"
)

type MainConfig struct {
	Logging    LogConfig         `yaml:"logging"`
	Database   database.Database `yaml:"database"`
	Server     ServerConfig      `yaml:"server"`
	PluginDirs []string          `yaml:"plugin_directories"`
}

func (config *MainConfig) Load(path string) error {
	data, err := ioutil.ReadFile(path)
	if err != nil {
		return err
	}

	return yaml.Unmarshal(data, config)
}

func (config *MainConfig) Save(path string) error {
	data, err := yaml.Marshal(config)
	if err != nil {
		return err
	}

	return ioutil.WriteFile(path, data, 0644)
}

type ServerConfig struct {
	Listen   string `yaml:"listen"`
	BasePath string `yaml:"base_path"`
}

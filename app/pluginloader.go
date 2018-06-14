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
	"fmt"
	"plugin"

	"maubot.xyz"
	"maubot.xyz/database"
)

type PluginWrapper struct {
	maubot.Plugin
	Creator *maubot.PluginCreator
	DB      *database.Plugin
}

func LoadPlugin(path string) (*maubot.PluginCreator, error) {
	rawPlugin, err := plugin.Open(path)
	if err != nil {
		return nil, fmt.Errorf("failed to open: %v", err)
	}

	pluginCreatorSymbol, err := rawPlugin.Lookup("Plugin")
	if err == nil {
		pluginCreator, ok := pluginCreatorSymbol.(*maubot.PluginCreator)
		if ok {
			pluginCreator.Path = path
			return pluginCreator, nil
		}
	}

	pluginCreatorFuncSymbol, err := rawPlugin.Lookup("Create")
	if err != nil {
		return nil, fmt.Errorf("symbol \"Create\" not found: %v", err)
	}
	pluginCreatorFunc, ok := pluginCreatorFuncSymbol.(maubot.PluginCreatorFunc)
	if !ok {
		return nil, fmt.Errorf("symbol \"Create\" does not implement maubot.PluginCreator")
	}

	nameSymbol, err := rawPlugin.Lookup("Name")
	if err != nil {
		return nil, fmt.Errorf("symbol \"Name\" not found: %v", err)
	}
	name, ok := nameSymbol.(string)
	if !ok {
		return nil, fmt.Errorf("symbol \"Name\" is not a string")
	}

	versionSymbol, err := rawPlugin.Lookup("Version")
	if err != nil {
		return nil, fmt.Errorf("symbol \"Version\" not found: %v", err)
	}
	version, ok := versionSymbol.(string)
	if !ok {
		return nil, fmt.Errorf("symbol \"Version\" is not a string")
	}

	return &maubot.PluginCreator{
		Create:  pluginCreatorFunc,
		Name:    name,
		Version: version,
		Path:    path,
	}, nil
}

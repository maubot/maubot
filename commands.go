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

type CommandHandler func(*Event) CommandHandlerResult

type CommandSpec struct {
	Commands        []Command        `json:"commands,omitempty"`
	PassiveCommands []PassiveCommand `json:"passive_commands,omitempty"`
}

func (spec *CommandSpec) Clone() *CommandSpec {
	return &CommandSpec{
		Commands:        append([]Command(nil), spec.Commands...),
		PassiveCommands: append([]PassiveCommand(nil), spec.PassiveCommands...),
	}
}

func (spec *CommandSpec) Merge(otherSpecs ...*CommandSpec) {
	for _, otherSpec := range otherSpecs {
		spec.Commands = append(spec.Commands, otherSpec.Commands...)
		spec.PassiveCommands = append(spec.PassiveCommands, otherSpec.PassiveCommands...)
	}
}

func (spec *CommandSpec) Equals(otherSpec *CommandSpec) bool {
	if otherSpec == nil ||
		len(spec.Commands) != len(otherSpec.Commands) ||
		len(spec.PassiveCommands) != len(otherSpec.PassiveCommands) {
		return false
	}

	for index, cmd := range spec.Commands {
		otherCmd := otherSpec.Commands[index]
		if !cmd.Equals(otherCmd) {
			return false
		}
	}

	for index, cmd := range spec.PassiveCommands {
		otherCmd := otherSpec.PassiveCommands[index]
		if !cmd.Equals(otherCmd) {
			return false
		}
	}

	return true
}

type Command struct {
	Syntax      string      `json:"syntax"`
	Description string      `json:"description,omitempty"`
	Arguments   ArgumentMap `json:"arguments"`
}

func (cmd Command) Equals(otherCmd Command) bool {
	return cmd.Syntax == otherCmd.Syntax &&
		cmd.Description == otherCmd.Description &&
		cmd.Arguments.Equals(otherCmd.Arguments)
}

type ArgumentMap map[string]Argument

func (argMap ArgumentMap) Equals(otherMap ArgumentMap) bool {
	if len(argMap) != len(otherMap) {
		return false
	}

	for name, argument := range argMap {
		otherArgument, ok := otherMap[name]
		if !ok || !argument.Equals(otherArgument) {
			return false
		}
	}
	return true
}

type Argument struct {
	Matches     string `json:"matches"`
	Required    bool   `json:"required"`
	Description string `json:"description,omitempty"`
}

func (arg Argument) Equals(otherArg Argument) bool {
	return arg.Matches == otherArg.Matches &&
		arg.Required == otherArg.Required &&
		arg.Description == otherArg.Description
}

// Common PassiveCommand MatchAgainst targets.
const (
	MatchAgainstBody = "body"
)

type PassiveCommand struct {
	Name         string `json:"name"`
	Matches      string `json:"matches"`
	MatchAgainst string `json:"match_against"`
	MatchEvent   *Event `json:"match_event"`
}

func (cmd PassiveCommand) Equals(otherCmd PassiveCommand) bool {
	return cmd.Name == otherCmd.Name &&
		cmd.Matches == otherCmd.Matches &&
		cmd.MatchAgainst == otherCmd.MatchAgainst &&
		((cmd.MatchEvent != nil && cmd.MatchEvent.Equals(otherCmd.MatchEvent)) || otherCmd.MatchEvent == nil)
}

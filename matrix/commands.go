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
	"fmt"
	"regexp"
	"strings"

	log "maunium.net/go/maulogger"

	"maubot.xyz"
)

type ParsedCommand struct {
	Name         string
	IsPassive    bool
	Arguments    []string
	StartsWith   string
	Matches      *regexp.Regexp
	MatchAgainst string
	MatchesEvent *maubot.Event
}

func (pc *ParsedCommand) parseCommandSyntax(command maubot.Command) error {
	regexBuilder := &strings.Builder{}
	swBuilder := &strings.Builder{}
	argumentEncountered := false

	regexBuilder.WriteRune('^')
	words := strings.Split(command.Syntax, " ")
	for i, word := range words {
		argument, ok := command.Arguments[word]
		// TODO enable $ check?
		if ok && len(word) > 0 /*&& word[0] == '$'*/ {
			argumentEncountered = true
			regex := argument.Matches
			if argument.Required {
				regex = fmt.Sprintf("(?:%s)?", regex)
			}
			pc.Arguments = append(pc.Arguments, word)
			regexBuilder.WriteString(regex)
		} else {
			if !argumentEncountered {
				swBuilder.WriteString(word)
			}
			regexBuilder.WriteString(regexp.QuoteMeta(word))
		}

		if i < len(words)-1 {
			if !argumentEncountered {
				swBuilder.WriteRune(' ')
			}
			regexBuilder.WriteRune(' ')
		}
	}
	regexBuilder.WriteRune('$')

	var err error
	pc.StartsWith = swBuilder.String()
	// Trim the extra space at the end added in the parse loop
	pc.StartsWith = pc.StartsWith[:len(pc.StartsWith)-1]
	pc.Matches, err = regexp.Compile(regexBuilder.String())
	pc.MatchAgainst = "body"
	return err
}

func (pc *ParsedCommand) parsePassiveCommandSyntax(command maubot.PassiveCommand) error {
	pc.MatchAgainst = command.MatchAgainst
	var err error
	pc.Matches, err = regexp.Compile(fmt.Sprintf("(%s)", command.Matches))
	pc.MatchesEvent = command.MatchEvent
	return err
}

func ParseSpec(spec *maubot.CommandSpec) (commands []*ParsedCommand) {
	for _, command := range spec.Commands {
		parsing := &ParsedCommand{
			Name:      command.Syntax,
			IsPassive: false,
		}
		err := parsing.parseCommandSyntax(command)
		if err != nil {
			log.Warnf("Failed to parse regex of command %s: %v\n", command.Syntax, err)
			continue
		}
		commands = append(commands, parsing)
	}
	for _, command := range spec.PassiveCommands {
		parsing := &ParsedCommand{
			Name:      command.Name,
			IsPassive: true,
		}
		err := parsing.parsePassiveCommandSyntax(command)
		if err != nil {
			log.Warnf("Failed to parse regex of passive command %s: %v\n", command.Name, err)
			continue
		}
		commands = append(commands, parsing)
	}
	return commands
}

func deepGet(from map[string]interface{}, path string) interface{} {
	for {
		dotIndex := strings.IndexRune(path, '.')
		if dotIndex == -1 {
			return from[path]
		}

		var key string
		key, path = path[:dotIndex], path[dotIndex+1:]
		var ok bool
		from, ok = from[key].(map[string]interface{})
		if !ok {
			return nil
		}
	}
}

func (pc *ParsedCommand) MatchActive(evt *maubot.Event) bool {
	if !strings.HasPrefix(evt.Content.Body, pc.StartsWith) {
		return false
	}
	match := pc.Matches.FindStringSubmatch(evt.Content.Body)
	if match == nil {
		return false
	}
	// First element is whole content
	match = match[1:]

	evt.Content.Command.Arguments = make(map[string]string)
	for i, value := range match {
		if i >= len(pc.Arguments) {
			break
		}
		key := pc.Arguments[i]
		evt.Content.Command.Arguments[key] = value
	}

	evt.Content.Command.Matched = pc.Name
	// TODO add evt.Content.Command.Target?

	return true
}

func (pc *ParsedCommand) MatchPassive(evt *maubot.Event) bool {
	matchAgainst, ok := deepGet(evt.Content.Raw, pc.MatchAgainst).(string)
	if !ok {
		matchAgainst = evt.Content.Body
	}

	if pc.MatchesEvent != nil && !pc.MatchesEvent.Equals(evt) {
		return false
	}

	matches := pc.Matches.FindAllStringSubmatch(matchAgainst, -1)
	if matches == nil {
		return false
	}

	values := make([]string, len(matches))
	for i, match := range matches {
		values[i] = match[0]
	}

	evt.Unsigned.PassiveCommand.Matched = pc.Name
	evt.Unsigned.PassiveCommand.Values = values

	return true
}

func (pc *ParsedCommand) Match(evt *maubot.Event) bool {
	if pc.IsPassive {
		return pc.MatchPassive(evt)
	} else {
		return pc.MatchActive(evt)
	}
}

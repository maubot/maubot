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

	"maubot.xyz"
	"maubot.xyz/database"
	"maunium.net/go/gomatrix"
	"maunium.net/go/gomatrix/format"
	log "maunium.net/go/maulogger"
)

type Client struct {
	*gomatrix.Client
	syncer   *MaubotSyncer
	handlers map[string][]maubot.CommandHandler
	commands []*ParsedCommand
	DB       *database.MatrixClient
}

func NewClient(db *database.MatrixClient) (*Client, error) {
	mxClient, err := gomatrix.NewClient(db.Homeserver, db.UserID, db.AccessToken)
	if err != nil {
		return nil, err
	}

	client := &Client{
		Client:   mxClient,
		handlers: make(map[string][]maubot.CommandHandler),
		commands: ParseSpec(db.Commands()),
		DB:       db,
	}

	client.syncer = NewMaubotSyncer(client, client.Store)
	client.Client.Syncer = client.syncer

	client.AddEventHandler(gomatrix.StateMember, client.onJoin)
	client.AddEventHandler(gomatrix.EventMessage, client.onMessage)

	return client, nil
}

func (client *Client) Proxy(owner string) *ClientProxy {
	return &ClientProxy{
		hiddenClient: client,
		owner:        owner,
	}
}

func (client *Client) AddEventHandler(evt gomatrix.EventType, handler maubot.EventHandler) {
	client.syncer.OnEventType(evt, func(evt *maubot.Event) maubot.EventHandlerResult {
		if evt.Sender == client.UserID {
			return maubot.StopEventPropagation
		}
		return handler(evt)
	})
}

func (client *Client) AddCommandHandler(owner, evt string, handler maubot.CommandHandler) {
	log.Debugln("Registering command handler for event", evt, "by", owner)
	list, ok := client.handlers[evt]
	if !ok {
		list = []maubot.CommandHandler{handler}
	} else {
		list = append(list, handler)
	}
	client.handlers[evt] = list
}

func (client *Client) SetCommandSpec(owner string, spec *maubot.CommandSpec) {
	log.Debugln("Registering command spec for", owner, "on", client.UserID)
	changed := client.DB.SetCommandSpec(owner, spec)
	if changed {
		client.commands = ParseSpec(client.DB.Commands())
		log.Debugln("Command spec of", owner, "on", client.UserID, "updated.")
	}
}

func (client *Client) GetEvent(roomID, eventID string) *maubot.Event {
	evt, err := client.Client.GetEvent(roomID, eventID)
	if err != nil {
		log.Warnf("Failed to get event %s @ %s: %v\n", eventID, roomID, err)
		return nil
	}
	return client.ParseEvent(evt)
}

func (client *Client) TriggerCommand(command *ParsedCommand, evt *maubot.Event) maubot.CommandHandlerResult {
	handlers, ok := client.handlers[command.Name]
	if !ok {
		log.Warnf("Command %s triggered by %s doesn't have any handlers.\n", command.Name, evt.Sender)
		return maubot.Continue
	}

	log.Debugf("Command %s on client %s triggered by %s\n", command.Name, client.UserID, evt.Sender)
	for _, handler := range handlers {
		result := handler(evt)
		if result == maubot.StopCommandPropagation {
			break
		} else if result != maubot.Continue {
			return result
		}
	}

	return maubot.Continue
}

func (client *Client) onMessage(evt *maubot.Event) maubot.EventHandlerResult {
	for _, command := range client.commands {
		if command.Match(evt.Event) {
			return client.TriggerCommand(command, evt)
		}
	}
	return maubot.Continue
}

func (client *Client) onJoin(evt *maubot.Event) maubot.EventHandlerResult {
	if client.DB.AutoJoinRooms && evt.GetStateKey() == client.DB.UserID && evt.Content.Membership == "invite" {
		client.JoinRoom(evt.RoomID)
		return maubot.StopEventPropagation
	}
	return maubot.Continue
}

func (client *Client) JoinRoom(roomID string) (resp *gomatrix.RespJoinRoom, err error) {
	return client.Client.JoinRoom(roomID, "", nil)
}

func (client *Client) SendMessage(roomID, text string) (string, error) {
	return client.SendContent(roomID, format.RenderMarkdown(text))
}

func (client *Client) SendMessagef(roomID, text string, args ...interface{}) (string, error) {
	return client.SendContent(roomID, format.RenderMarkdown(fmt.Sprintf(text, args...)))
}

func (client *Client) SendContent(roomID string, content gomatrix.Content) (string, error) {
	return client.SendMessageEvent(roomID, gomatrix.EventMessage, content)
}

func (client *Client) SendMessageEvent(roomID string, evtType gomatrix.EventType, content interface{}) (string, error) {
	resp, err := client.Client.SendMessageEvent(roomID, evtType, content)
	if err != nil {
		return "", err
	}
	return resp.EventID, nil
}

func (client *Client) Sync() {
	go func() {
		err := client.Client.Sync()
		if err != nil {
			log.Errorln("Sync() in client", client.UserID, "errored:", err)
		}
	}()
}

type hiddenClient = Client

type ClientProxy struct {
	*hiddenClient
	owner string
}

func (cp *ClientProxy) AddCommandHandler(evt string, handler maubot.CommandHandler) {
	cp.hiddenClient.AddCommandHandler(cp.owner, evt, handler)
}

func (cp *ClientProxy) SetCommandSpec(spec *maubot.CommandSpec) {
	cp.hiddenClient.SetCommandSpec(cp.owner, spec)
}

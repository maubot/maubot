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
	"io"

	"maunium.net/go/gomatrix"
)

type EventHandler func(*Event) EventHandlerResult
type EventHandlerResult int
type CommandHandlerResult = EventHandlerResult

const (
	Continue EventHandlerResult = iota
	StopEventPropagation
	StopCommandPropagation CommandHandlerResult = iota
)

type GomatrixClient interface {
	//d <method> = disabled
	//r <method> = replaced

	BanUser(roomID string, req *gomatrix.ReqBanUser) (resp *gomatrix.RespBanUser, err error)
	//d BuildBaseURL(urlPath ...string) string
	//d BuildURL(urlPath ...string) string
	//d BuildURLWithQuery(urlPath []string, urlQuery map[string]string) string
	//d ClearCredentials()
	//d CreateFilter(filter json.RawMessage) (resp *gomatrix.RespCreateFilter, err error)
	CreateRoom(req *gomatrix.ReqCreateRoom) (resp *gomatrix.RespCreateRoom, err error)
	Download(mxcURL string) (io.ReadCloser, error)
	DownloadBytes(mxcURL string) ([]byte, error)
	ForgetRoom(roomID string) (resp *gomatrix.RespForgetRoom, err error)
	GetAvatarURL() (url string, err error)
	GetDisplayName(mxid string) (resp *gomatrix.RespUserDisplayName, err error)
	//r GetEvent(roomID, eventID string) (resp *gomatrix.Event, err error)
	GetOwnDisplayName() (resp *gomatrix.RespUserDisplayName, err error)
	InviteUser(roomID string, req *gomatrix.ReqInviteUser) (resp *gomatrix.RespInviteUser, err error)
	InviteUserByThirdParty(roomID string, req *gomatrix.ReqInvite3PID) (resp *gomatrix.RespInviteUser, err error)
	//r JoinRoom(roomIDorAlias, serverName string, content interface{}) (resp *gomatrix.RespJoinRoom, err error)
	JoinedMembers(roomID string) (resp *gomatrix.RespJoinedMembers, err error)
	JoinedRooms() (resp *gomatrix.RespJoinedRooms, err error)
	KickUser(roomID string, req *gomatrix.ReqKickUser) (resp *gomatrix.RespKickUser, err error)
	LeaveRoom(roomID string) (resp *gomatrix.RespLeaveRoom, err error)
	//d Login(req *gomatrix.ReqLogin) (resp *gomatrix.RespLogin, err error)
	//d Logout() (resp *gomatrix.RespLogout, err error)
	MakeRequest(method string, httpURL string, reqBody interface{}, resBody interface{}) ([]byte, error)
	MarkRead(roomID, eventID string) (err error)
	Messages(roomID, from, to string, dir rune, limit int) (resp *gomatrix.RespMessages, err error)
	RedactEvent(roomID, eventID string, req *gomatrix.ReqRedact) (resp *gomatrix.RespSendEvent, err error)
	//d Register(req *gomatrix.ReqRegister) (*gomatrix.RespRegister, *gomatrix.RespUserInteractive, error)
	//d RegisterDummy(req *gomatrix.ReqRegister) (*gomatrix.RespRegister, error)
	//d RegisterGuest(req *gomatrix.ReqRegister) (*gomatrix.RespRegister, *gomatrix.RespUserInteractive, error)
	SendImage(roomID, body, url string) (*gomatrix.RespSendEvent, error)
	//SendMassagedMessageEvent(roomID string, eventType gomatrix.EventType, contentJSON interface{}, ts int64) (resp *gomatrix.RespSendEvent, err error)
	//SendMassagedStateEvent(roomID string, eventType gomatrix.EventType, stateKey string, contentJSON interface{}, ts int64) (resp *gomatrix.RespSendEvent, err error)
	//r SendMessageEvent(roomID string, eventType gomatrix.EventType, contentJSON interface{}) (resp *gomatrix.RespSendEvent, err error)
	SendNotice(roomID, text string) (*gomatrix.RespSendEvent, error)
	SendStateEvent(roomID string, eventType gomatrix.EventType, stateKey string, contentJSON interface{}) (resp *gomatrix.RespSendEvent, err error)
	SendText(roomID, text string) (*gomatrix.RespSendEvent, error)
	SendVideo(roomID, body, url string) (*gomatrix.RespSendEvent, error)
	SetAvatarURL(url string) (err error)
	SetCredentials(userID, accessToken string)
	SetDisplayName(displayName string) (err error)
	SetPresence(status string) (err error)
	StateEvent(roomID string, eventType gomatrix.EventType, stateKey string, outContent interface{}) (err error)
	//d StopSync()
	//d Sync() error
	//d SyncRequest(timeout int, since, filterID string, fullState bool, setPresence string) (resp *gomatrix.RespSync, err error)
	TurnServer() (resp *gomatrix.RespTurnServer, err error)
	UnbanUser(roomID string, req *gomatrix.ReqUnbanUser) (resp *gomatrix.RespUnbanUser, err error)
	Upload(content io.Reader, contentType string, contentLength int64) (*gomatrix.RespMediaUpload, error)
	UploadBytes(data []byte, contentType string) (*gomatrix.RespMediaUpload, error)
	UploadLink(link string) (*gomatrix.RespMediaUpload, error)
	UserTyping(roomID string, typing bool, timeout int64) (resp *gomatrix.RespTyping, err error)
	Versions() (resp *gomatrix.RespVersions, err error)
}

type MBMatrixClient interface {
	AddEventHandler(gomatrix.EventType, EventHandler)
	AddCommandHandler(string, CommandHandler)
	SetCommandSpec(*CommandSpec)

	GetEvent(roomID, eventID string) *Event
	JoinRoom(roomIDOrAlias string) (resp *gomatrix.RespJoinRoom, err error)
	SendMessage(roomID, text string) (eventID string, err error)
	SendMessagef(roomID, text string, args ...interface{}) (eventID string, err error)
	SendContent(roomID string, content gomatrix.Content) (eventID string, err error)
	SendMessageEvent(roomID string, evtType gomatrix.EventType, content interface{}) (eventID string, err error)
}

type MatrixClient interface {
	GomatrixClient
	MBMatrixClient
}

type EventFuncs interface {
	MarkRead() error
	Reply(string) (string, error)
	ReplyContent(gomatrix.Content) (string, error)
	SendMessage(string) (string, error)
	SendMessagef(string, ...interface{}) (string, error)
	SendContent(gomatrix.Content) (string, error)
	SendMessageEvent(evtType gomatrix.EventType, content interface{}) (eventID string, err error)
}

type Event struct {
	EventFuncs
	*gomatrix.Event
}

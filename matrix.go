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

type EventType string
type MessageType string

// State events
const (
	StateAliases        EventType = "m.room.aliases"
	StateCanonicalAlias           = "m.room.canonical_alias"
	StateCreate                   = "m.room.create"
	StateJoinRules                = "m.room.join_rules"
	StateMember                   = "m.room.member"
	StatePowerLevels              = "m.room.power_levels"
	StateRoomName                 = "m.room.name"
	StateTopic                    = "m.room.topic"
	StateRoomAvatar               = "m.room.avatar"
	StatePinnedEvents             = "m.room.pinned_events"
)

// Message events
const (
	EventRedaction EventType = "m.room.redaction"
	EventMessage             = "m.room.message"
	EventSticker             = "m.sticker"
)

// Msgtypes
const (
	MsgText     MessageType = "m.text"
	MsgEmote                = "m.emote"
	MsgNotice               = "m.notice"
	MsgImage                = "m.image"
	MsgLocation             = "m.location"
	MsgVideo                = "m.video"
	MsgAudio                = "m.audio"
)

const FormatHTML = "org.matrix.custom.html"

type EventHandler func(*Event) EventHandlerResult
type EventHandlerResult bool

const (
	Continue        EventHandlerResult = false
	StopPropagation EventHandlerResult = true
)

type MatrixClient interface {
	AddEventHandler(EventType, EventHandler)
	AddCommandHandler(string, CommandHandler)
	SetCommandSpec(*CommandSpec)
	GetEvent(string, string) *Event
}

type EventFuncs interface {
	MarkRead() error
	Reply(string) (string, error)
	ReplyContent(Content) (string, error)
	SendMessage(string) (string, error)
	SendContent(Content) (string, error)
	SendRawEvent(EventType, interface{}) (string, error)
}

type Event struct {
	EventFuncs

	StateKey  string    `json:"state_key,omitempty"` // The state key for the event. Only present on State Events.
	Sender    string    `json:"sender"`              // The user ID of the sender of the event
	Type      EventType `json:"type"`                // The event type
	Timestamp int64     `json:"origin_server_ts"`    // The unix timestamp when this message was sent by the origin server
	ID        string    `json:"event_id"`            // The unique ID of this event
	RoomID    string    `json:"room_id"`             // The room the event was sent to. May be nil (e.g. for presence)
	Content   Content   `json:"content"`
	Redacts   string    `json:"redacts,omitempty"`  // The event ID that was redacted if a m.room.redaction event
	Unsigned  Unsigned  `json:"unsigned,omitempty"` // Unsigned content set by own homeserver.
}

func (evt *Event) Equals(otherEvt *Event) bool {
	return evt.StateKey == otherEvt.StateKey &&
		evt.Sender == otherEvt.Sender &&
		evt.Type == otherEvt.Type &&
		evt.Timestamp == otherEvt.Timestamp &&
		evt.ID == otherEvt.ID &&
		evt.RoomID == otherEvt.RoomID &&
		evt.Content.Equals(&otherEvt.Content) &&
		evt.Redacts == otherEvt.Redacts &&
		evt.Unsigned.Equals(&otherEvt.Unsigned)
}

type Unsigned struct {
	PrevContent   *Content `json:"prev_content,omitempty"`
	PrevSender    string   `json:"prev_sender,omitempty"`
	ReplacesState string   `json:"replaces_state,omitempty"`
	Age           int64    `json:"age"`
}

func (unsigned Unsigned) Equals(otherUnsigned *Unsigned) bool {
	return unsigned.PrevContent.Equals(otherUnsigned.PrevContent) &&
		unsigned.PrevSender == otherUnsigned.PrevSender &&
		unsigned.ReplacesState == otherUnsigned.ReplacesState &&
		unsigned.Age == otherUnsigned.Age
}

type Content struct {
	Raw map[string]interface{} `json:"-"`

	MsgType       MessageType `json:"msgtype"`
	Body          string      `json:"body"`
	Format        string      `json:"format,omitempty"`
	FormattedBody string      `json:"formatted_body,omitempty"`

	Info *FileInfo `json:"info,omitempty"`
	URL  string    `json:"url,omitempty"`

	Membership string `json:"membership,omitempty"`

	RelatesTo RelatesTo `json:"m.relates_to,omitempty"`
}

func (content Content) Equals(otherContent *Content) bool {
	return content.MsgType == otherContent.MsgType &&
		content.Body == otherContent.Body &&
		content.Format == otherContent.Format &&
		content.FormattedBody == otherContent.FormattedBody &&
		((content.Info != nil && content.Info.Equals(otherContent.Info)) || otherContent.Info == nil) &&
		content.URL == otherContent.URL &&
		content.Membership == otherContent.Membership &&
		content.RelatesTo == otherContent.RelatesTo
}

type FileInfo struct {
	MimeType      string    `json:"mimetype,omitempty"`
	ThumbnailInfo *FileInfo `json:"thumbnail_info,omitempty"`
	ThumbnailURL  string    `json:"thumbnail_url,omitempty"`
	Height        int       `json:"h,omitempty"`
	Width         int       `json:"w,omitempty"`
	Size          int       `json:"size,omitempty"`
}

func (fi *FileInfo) Equals(otherFI *FileInfo) bool {
	return fi.MimeType == otherFI.MimeType &&
		fi.ThumbnailURL == otherFI.ThumbnailURL &&
		fi.Height == otherFI.Height &&
		fi.Width == otherFI.Width &&
		fi.Size == otherFI.Size &&
		((fi.ThumbnailInfo != nil && fi.ThumbnailInfo.Equals(otherFI.ThumbnailInfo)) || otherFI.ThumbnailInfo == nil)
}

type RelatesTo struct {
	InReplyTo InReplyTo `json:"m.in_reply_to,omitempty"`
}

type InReplyTo struct {
	EventID string `json:"event_id"`
	// Not required, just for future-proofing
	RoomID string `json:"room_id,omitempty"`
}

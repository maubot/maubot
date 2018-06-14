package interfaces

type Plugin interface {
	Start()
	Stop()
}

type EventHandler func(*Event) bool

type MatrixClient interface {
	AddEventHandler(string, EventHandler)
}

type EventFuncs interface {
	Reply(text string) (string, error)
	SendMessage(text string) (string, error)
	SendEvent(content map[string]interface{}) (string, error)
}

type Event struct {
	EventFuncs

	StateKey  string                 `json:"state_key,omitempty"` // The state key for the event. Only present on State Events.
	Sender    string                 `json:"sender"`              // The user ID of the sender of the event
	Type      string                 `json:"type"`                // The event type
	Timestamp int64                  `json:"origin_server_ts"`    // The unix timestamp when this message was sent by the origin server
	ID        string                 `json:"event_id"`            // The unique ID of this event
	RoomID    string                 `json:"room_id"`             // The room the event was sent to. May be nil (e.g. for presence)
	Content   map[string]interface{} `json:"content"`             // The JSON content of the event.
	Redacts   string                 `json:"redacts,omitempty"`   // The event ID that was redacted if a m.room.redaction event
	Unsigned  Unsigned               `json:"unsigned,omitempty"`  // Unsigned content set by own homeserver.
}

type Unsigned struct {
	PrevContent   map[string]interface{} `json:"prev_content,omitempty"`
	PrevSender    string                 `json:"prev_sender,omitempty"`
	ReplacesState string                 `json:"replaces_state,omitempty"`
	Age           int64                  `json:"age"`
}

type PluginCreatorFunc func(client MatrixClient) Plugin

type PluginCreator struct {
	Create  PluginCreatorFunc
	Name    string
	Version string
	Path    string
}

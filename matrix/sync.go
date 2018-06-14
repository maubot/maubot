package matrix

import (
	"encoding/json"
	"fmt"
	"runtime/debug"
	"time"

	"maubot.xyz/interfaces"
	"maunium.net/go/gomatrix"
)

type MaubotSyncer struct {
	Client    *Client
	Store     gomatrix.Storer
	listeners map[string][]interfaces.EventHandler
}

// NewDefaultSyncer returns an instantiated DefaultSyncer
func NewMaubotSyncer(client *Client, store gomatrix.Storer) *MaubotSyncer {
	return &MaubotSyncer{
		Client:    client,
		Store:     store,
		listeners: make(map[string][]interfaces.EventHandler),
	}
}

// ProcessResponse processes the /sync response in a way suitable for bots. "Suitable for bots" means a stream of
// unrepeating events. Returns a fatal error if a listener panics.
func (s *MaubotSyncer) ProcessResponse(res *gomatrix.RespSync, since string) (err error) {
	if !s.shouldProcessResponse(res, since) {
		return
	}

	defer func() {
		if r := recover(); r != nil {
			err = fmt.Errorf("ProcessResponse panicked! userID=%s since=%s panic=%s\n%s", s.Client.UserID, since, r, debug.Stack())
		}
	}()

	for roomID, roomData := range res.Rooms.Join {
		room := s.getOrCreateRoom(roomID)
		for _, event := range roomData.State.Events {
			event.RoomID = roomID
			room.UpdateState(event)
			s.notifyListeners(event)
		}
		for _, event := range roomData.Timeline.Events {
			event.RoomID = roomID
			s.notifyListeners(event)
		}
	}
	for roomID, roomData := range res.Rooms.Invite {
		room := s.getOrCreateRoom(roomID)
		for _, event := range roomData.State.Events {
			event.RoomID = roomID
			room.UpdateState(event)
			s.notifyListeners(event)
		}
	}
	for roomID, roomData := range res.Rooms.Leave {
		room := s.getOrCreateRoom(roomID)
		for _, event := range roomData.Timeline.Events {
			if event.StateKey != nil {
				event.RoomID = roomID
				room.UpdateState(event)
				s.notifyListeners(event)
			}
		}
	}
	return
}

// OnEventType allows callers to be notified when there are new events for the given event type.
// There are no duplicate checks.
func (s *MaubotSyncer) OnEventType(eventType string, callback interfaces.EventHandler) {
	_, exists := s.listeners[eventType]
	if !exists {
		s.listeners[eventType] = []interfaces.EventHandler{}
	}
	s.listeners[eventType] = append(s.listeners[eventType], callback)
}

// shouldProcessResponse returns true if the response should be processed. May modify the response to remove
// stuff that shouldn't be processed.
func (s *MaubotSyncer) shouldProcessResponse(resp *gomatrix.RespSync, since string) bool {
	if since == "" {
		return false
	}
	// This is a horrible hack because /sync will return the most recent messages for a room
	// as soon as you /join it. We do NOT want to process those events in that particular room
	// because they may have already been processed (if you toggle the bot in/out of the room).
	//
	// Work around this by inspecting each room's timeline and seeing if an m.room.member event for us
	// exists and is "join" and then discard processing that room entirely if so.
	// TODO: We probably want to process messages from after the last join event in the timeline.
	for roomID, roomData := range resp.Rooms.Join {
		for i := len(roomData.Timeline.Events) - 1; i >= 0; i-- {
			e := roomData.Timeline.Events[i]
			if e.Type == "m.room.member" && e.StateKey != nil && *e.StateKey == s.Client.UserID {
				m := e.Content["membership"]
				mship, ok := m.(string)
				if !ok {
					continue
				}
				if mship == "join" {
					_, ok := resp.Rooms.Join[roomID]
					if !ok {
						continue
					}
					delete(resp.Rooms.Join, roomID)   // don't re-process messages
					delete(resp.Rooms.Invite, roomID) // don't re-process invites
					break
				}
			}
		}
	}
	return true
}

// getOrCreateRoom must only be called by the Sync() goroutine which calls ProcessResponse()
func (s *MaubotSyncer) getOrCreateRoom(roomID string) *gomatrix.Room {
	room := s.Store.LoadRoom(roomID)
	if room == nil {
		room = gomatrix.NewRoom(roomID)
		s.Store.SaveRoom(room)
	}
	return room
}

func (s *MaubotSyncer) notifyListeners(mxEvent *gomatrix.Event) {
	event := s.Client.ParseEvent(mxEvent)
	listeners, exists := s.listeners[event.Type]
	if !exists {
		return
	}
	for _, fn := range listeners {
		if !fn(event.Interface()) {
			break
		}
	}
}

// OnFailedSync always returns a 10 second wait period between failed /syncs, never a fatal error.
func (s *MaubotSyncer) OnFailedSync(res *gomatrix.RespSync, err error) (time.Duration, error) {
	return 10 * time.Second, nil
}

// GetFilterJSON returns a filter with a timeline limit of 50.
func (s *MaubotSyncer) GetFilterJSON(userID string) json.RawMessage {
	return json.RawMessage(`{"room":{"timeline":{"limit":50}}}`)
}

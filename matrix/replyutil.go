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
	"regexp"
	"strings"
	"fmt"
	"maunium.net/go/gomatrix"
	"golang.org/x/net/html"
)

var HTMLReplyFallbackRegex = regexp.MustCompile(`^<mx-reply>[\s\S]+?</mx-reply>`)

func TrimReplyFallbackHTML(html string) string {
	return HTMLReplyFallbackRegex.ReplaceAllString(html, "")
}

func TrimReplyFallbackText(text string) string {
	if !strings.HasPrefix(text, "> ") || !strings.Contains(text, "\n") {
		return text
	}

	lines := strings.Split(text, "\n")
	for len(lines) > 0 && strings.HasPrefix(lines[0], "> ") {
		lines = lines[1:]
	}
	return strings.Join(lines, "\n")
}

func RemoveReplyFallback(evt *gomatrix.Event) {
	if format, ok := evt.Content["format"].(string); ok && format == "org.matrix.custom.html" {
		htmlBody, _ := evt.Content["formatted_body"].(string)
		evt.Content["formatted_body"] = TrimReplyFallbackHTML(htmlBody)
	}
	plainBody, _ := evt.Content["body"].(string)
	evt.Content["body"] = TrimReplyFallbackText(plainBody)
}

const ReplyFormat = `<mx-reply><blockquote>
<a href="https://matrix.to/#/%s/%s">In reply to</a>
<a href="https://matrix.to/#/%s">%s</a>
%s
</blockquote></mx-reply>
`

func ReplyFallbackHTML(evt *gomatrix.Event) string {
	body, ok := evt.Content["formatted_body"].(string)
	if !ok {
		body, _ = evt.Content["body"].(string)
		body = html.EscapeString(body)
	}

	senderDisplayName := evt.Sender

	return fmt.Sprintf(ReplyFormat, evt.RoomID, evt.ID, evt.Sender, senderDisplayName, body)
}

func ReplyFallbackText(evt *gomatrix.Event) string {
	body, _ := evt.Content["body"].(string)
	lines := strings.Split(strings.TrimSpace(body), "\n")
	firstLine, lines := lines[0], lines[1:]

	senderDisplayName := evt.Sender

	var fallbackText strings.Builder
	fmt.Fprintf(&fallbackText, "> <%s> %s", senderDisplayName, firstLine)
	for _, line := range lines {
		fmt.Fprintf(&fallbackText, "\n> %s", line)
	}
	fallbackText.WriteString("\n\n")
	return fallbackText.String()
}

func SetReply(content map[string]interface{}, inReplyTo *gomatrix.Event) map[string]interface{} {
	content["m.relates_to"] = map[string]interface{}{
		"m.in_reply_to": map[string]interface{}{
			"event_id": inReplyTo.ID,
			"room_id":  inReplyTo.RoomID,
		},
	}

	body, _ := content["body"].(string)
	content["body"] = ReplyFallbackText(inReplyTo) + body

	htmlBody, ok := content["formatted_body"].(string)
	if !ok {
		htmlBody = html.EscapeString(body)
		content["format"] = "org.matrix.custom.html"
	}
	content["formatted_body"] = ReplyFallbackHTML(inReplyTo) + htmlBody
	return content
}

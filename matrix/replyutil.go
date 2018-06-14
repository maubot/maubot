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

	"golang.org/x/net/html"
	"maubot.xyz"
	"maunium.net/go/gomatrix"
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
	return strings.TrimSpace(strings.Join(lines, "\n"))
}

func RemoveReplyFallback(evt *maubot.Event) {
	if len(evt.Content.RelatesTo.InReplyTo.EventID) > 0 {
		if evt.Content.Format == maubot.FormatHTML {
			evt.Content.FormattedBody = TrimReplyFallbackHTML(evt.Content.FormattedBody)
		}
		evt.Content.Body = TrimReplyFallbackText(evt.Content.Body)
	}
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

func SetReply(content maubot.Content, inReplyTo *gomatrix.Event) maubot.Content {
	content.RelatesTo.InReplyTo.EventID = inReplyTo.ID
	content.RelatesTo.InReplyTo.RoomID = inReplyTo.RoomID

	if content.MsgType == maubot.MsgText || content.MsgType == maubot.MsgNotice {
		if len(content.FormattedBody) == 0 || content.Format != maubot.FormatHTML {
			content.FormattedBody = html.EscapeString(content.Body)
			content.Format = maubot.FormatHTML
		}
		content.FormattedBody = ReplyFallbackHTML(inReplyTo) + content.FormattedBody
		content.Body = ReplyFallbackText(inReplyTo) + content.Body
	}

	return content
}

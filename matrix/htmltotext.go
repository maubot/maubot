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
	"math"
	"regexp"
	"strings"

	"golang.org/x/net/html"
	"strconv"
)

var matrixToURL = regexp.MustCompile("^(?:https?://)?(?:www\\.)?matrix\\.to/#/([#@!].*)")

type htmlParser struct {}

type taggedString struct {
	string
	tag string
}

func (parser *htmlParser) getAttribute(node *html.Node, attribute string) string {
	for _, attr := range node.Attr {
		if attr.Key == attribute {
			return attr.Val
		}
	}
	return ""
}

func digits(num int) int {
	return int(math.Floor(math.Log10(float64(num))) + 1)
}

func (parser *htmlParser) listToString(node *html.Node, stripLinebreak bool) string {
	ordered := node.Data == "ol"
	taggedChildren := parser.nodeToTaggedStrings(node.FirstChild, stripLinebreak)
	counter := 1
	indentLength := 0
	if ordered {
		start := parser.getAttribute(node, "start")
		if len(start) > 0 {
			counter, _ = strconv.Atoi(start)
		}

		longestIndex := (counter - 1) + len(taggedChildren)
		indentLength = digits(longestIndex)
	}
	indent := strings.Repeat(" ", indentLength+2)
	var children []string
	for _, child := range taggedChildren {
		if child.tag != "li" {
			continue
		}
		var prefix string
		if ordered {
			indexPadding := indentLength - digits(counter)
			prefix = fmt.Sprintf("%d. %s", counter, strings.Repeat(" ", indexPadding))
		} else {
			prefix = "● "
		}
		str := prefix + child.string
		counter++
		parts := strings.Split(str, "\n")
		for i, part := range parts[1:] {
			parts[i+1] = indent + part
		}
		str = strings.Join(parts, "\n")
		children = append(children, str)
	}
	return strings.Join(children, "\n")
}

func (parser *htmlParser) basicFormatToString(node *html.Node, stripLinebreak bool) string {
	str := parser.nodeToTagAwareString(node.FirstChild, stripLinebreak)
	switch node.Data {
	case "b", "strong":
		return fmt.Sprintf("**%s**", str)
	case "i", "em":
		return fmt.Sprintf("_%s_", str)
	case "s", "del":
		return fmt.Sprintf("~~%s~~", str)
	}
	return str
}

func (parser *htmlParser) headerToString(node *html.Node, stripLinebreak bool) string {
	children := parser.nodeToStrings(node.FirstChild, stripLinebreak)
	length := int(node.Data[1] - '0')
	prefix := strings.Repeat("#", length) + " "
	return prefix + strings.Join(children, "")
}

func (parser *htmlParser) blockquoteToString(node *html.Node, stripLinebreak bool) string {
	str := parser.nodeToTagAwareString(node.FirstChild, stripLinebreak)
	childrenArr := strings.Split(strings.TrimSpace(str), "\n")
	for index, child := range childrenArr {
		childrenArr[index] = "> " + child
	}
	return strings.Join(childrenArr, "\n")
}

func (parser *htmlParser) linkToString(node *html.Node, stripLinebreak bool) string {
	str := parser.nodeToTagAwareString(node.FirstChild, stripLinebreak)
	href := parser.getAttribute(node, "href")
	if len(href) == 0 {
		return str
	}
	match := matrixToURL.FindStringSubmatch(href)
	if len(match) == 2 {
//		pillTarget := match[1]
//		if pillTarget[0] == '@' {
//			if member := parser.room.GetMember(pillTarget); member != nil {
//				return member.DisplayName
//			}
//		}
//		return pillTarget
		return str
	}
	return fmt.Sprintf("%s (%s)", str, href)
}

func (parser *htmlParser) tagToString(node *html.Node, stripLinebreak bool) string {
	switch node.Data {
	case "blockquote":
		return parser.blockquoteToString(node, stripLinebreak)
	case "ol", "ul":
		return parser.listToString(node, stripLinebreak)
	case "h1", "h2", "h3", "h4", "h5", "h6":
		return parser.headerToString(node, stripLinebreak)
	case "br":
		return "\n"
	case "b", "strong", "i", "em", "s", "del", "u", "ins":
		return parser.basicFormatToString(node, stripLinebreak)
	case "a":
		return parser.linkToString(node, stripLinebreak)
	case "p":
		return parser.nodeToTagAwareString(node.FirstChild, stripLinebreak) + "\n"
	case "pre":
		return parser.nodeToString(node.FirstChild, false)
	default:
		return parser.nodeToTagAwareString(node.FirstChild, stripLinebreak)
	}
}

func (parser *htmlParser) singleNodeToString(node *html.Node, stripLinebreak bool) taggedString {
	switch node.Type {
	case html.TextNode:
		if stripLinebreak {
			node.Data = strings.Replace(node.Data, "\n", "", -1)
		}
		return taggedString{node.Data, "text"}
	case html.ElementNode:
		return taggedString{parser.tagToString(node, stripLinebreak), node.Data}
	case html.DocumentNode:
		return taggedString{parser.nodeToTagAwareString(node.FirstChild, stripLinebreak), "html"}
	default:
		return taggedString{"", "unknown"}
	}
}

func (parser *htmlParser) nodeToTaggedStrings(node *html.Node, stripLinebreak bool) (strs []taggedString) {
	for ; node != nil; node = node.NextSibling {
		strs = append(strs, parser.singleNodeToString(node, stripLinebreak))
	}
	return
}

var BlockTags = []string{"p", "h1", "h2", "h3", "h4", "h5", "h6", "ol", "ul", "pre", "blockquote", "div", "hr", "table"}

func (parser *htmlParser) isBlockTag(tag string) bool {
	for _, blockTag := range BlockTags {
		if tag == blockTag {
			return true
		}
	}
	return false
}

func (parser *htmlParser) nodeToTagAwareString(node *html.Node, stripLinebreak bool) string {
	strs := parser.nodeToTaggedStrings(node, stripLinebreak)
	var output strings.Builder
	for _, str := range strs {
		tstr := str.string
		if parser.isBlockTag(str.tag) {
			tstr = fmt.Sprintf("\n%s\n", tstr)
		}
		output.WriteString(tstr)
	}
	return strings.TrimSpace(output.String())
}

func (parser *htmlParser) nodeToStrings(node *html.Node, stripLinebreak bool) (strs []string) {
	for ; node != nil; node = node.NextSibling {
		strs = append(strs, parser.singleNodeToString(node, stripLinebreak).string)
	}
	return
}

func (parser *htmlParser) nodeToString(node *html.Node, stripLinebreak bool) string {
	return strings.Join(parser.nodeToStrings(node, stripLinebreak), "")
}

func (parser *htmlParser) Parse(htmlData string) string {
	node, _ := html.Parse(strings.NewReader(htmlData))
	return parser.nodeToTagAwareString(node, true)
}

func HTMLToText(html string) string {
	html = strings.Replace(html, "\t", "    ", -1)
	str := (&htmlParser{}).Parse(html)
	return str
}

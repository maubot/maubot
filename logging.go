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

type Logger interface {
	Write(p []byte) (n int, err error)
	Debug(parts ...interface{})
	Debugln(parts ...interface{})
	Debugf(message string, args ...interface{})
	Debugfln(message string, args ...interface{})
	Info(parts ...interface{})
	Infoln(parts ...interface{})
	Infof(message string, args ...interface{})
	Infofln(message string, args ...interface{})
	Warn(parts ...interface{})
	Warnln(parts ...interface{})
	Warnf(message string, args ...interface{})
	Warnfln(message string, args ...interface{})
	Error(parts ...interface{})
	Errorln(parts ...interface{})
	Errorf(message string, args ...interface{})
	Errorfln(message string, args ...interface{})
	Fatal(parts ...interface{})
	Fatalln(parts ...interface{})
	Fatalf(message string, args ...interface{})
	Fatalfln(message string, args ...interface{})
}

// mauLogger - A logger for Go programs
// Copyright (C) 2016 Tulir Asokan
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.

// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.

// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.

// Package maulogger ...
package maulogger

import (
	"os"
)

// DefaultLogger ...
var DefaultLogger = Create()

// SetWriter formats the given parts with fmt.Sprint and log them with the SetWriter level
func SetWriter(w *os.File) {
	DefaultLogger.SetWriter(w)
}

// OpenFile formats the given parts with fmt.Sprint and log them with the OpenFile level
func OpenFile() error {
	return DefaultLogger.OpenFile()
}

// Close formats the given parts with fmt.Sprint and log them with the Close level
func Close() {
	DefaultLogger.Close()
}

// CreateSublogger creates a Sublogger
func CreateSublogger(module string, DefaultLevel Level) *Sublogger {
	return DefaultLogger.CreateSublogger(module, DefaultLevel)
}

// Raw formats the given parts with fmt.Sprint and log them with the Raw level
func Raw(level Level, module, message string) {
	DefaultLogger.Raw(level, module, message)
}

// Log formats the given parts with fmt.Sprint and log them with the Log level
func Log(level Level, parts ...interface{}) {
	DefaultLogger.DefaultSub.Log(level, parts...)
}

// Logln formats the given parts with fmt.Sprintln and log them with the Log level
func Logln(level Level, parts ...interface{}) {
	DefaultLogger.DefaultSub.Logln(level, parts...)
}

// Logf formats the given message and args with fmt.Sprintf and log them with the Log level
func Logf(level Level, message string, args ...interface{}) {
	DefaultLogger.DefaultSub.Logf(level, message, args...)
}

// Debug formats the given parts with fmt.Sprint and log them with the Debug level
func Debug(parts ...interface{}) {
	DefaultLogger.DefaultSub.Debug(parts...)
}

// Debugln formats the given parts with fmt.Sprintln and log them with the Debug level
func Debugln(parts ...interface{}) {
	DefaultLogger.DefaultSub.Debugln(parts...)
}

// Debugf formats the given message and args with fmt.Sprintf and log them with the Debug level
func Debugf(message string, args ...interface{}) {
	DefaultLogger.DefaultSub.Debugf(message, args...)
}

// Info formats the given parts with fmt.Sprint and log them with the Info level
func Info(parts ...interface{}) {
	DefaultLogger.DefaultSub.Info(parts...)
}

// Infoln formats the given parts with fmt.Sprintln and log them with the Info level
func Infoln(parts ...interface{}) {
	DefaultLogger.DefaultSub.Infoln(parts...)
}

// Infof formats the given message and args with fmt.Sprintf and log them with the Info level
func Infof(message string, args ...interface{}) {
	DefaultLogger.DefaultSub.Infof(message, args...)
}

// Warn formats the given parts with fmt.Sprint and log them with the Warn level
func Warn(parts ...interface{}) {
	DefaultLogger.DefaultSub.Warn(parts...)
}

// Warnln formats the given parts with fmt.Sprintln and log them with the Warn level
func Warnln(parts ...interface{}) {
	DefaultLogger.DefaultSub.Warnln(parts...)
}

// Warnf formats the given message and args with fmt.Sprintf and log them with the Warn level
func Warnf(message string, args ...interface{}) {
	DefaultLogger.DefaultSub.Warnf(message, args...)
}

// Error formats the given parts with fmt.Sprint and log them with the Error level
func Error(parts ...interface{}) {
	DefaultLogger.DefaultSub.Error(parts...)
}

// Errorln formats the given parts with fmt.Sprintln and log them with the Error level
func Errorln(parts ...interface{}) {
	DefaultLogger.DefaultSub.Errorln(parts...)
}

// Errorf formats the given message and args with fmt.Sprintf and log them with the Error level
func Errorf(message string, args ...interface{}) {
	DefaultLogger.DefaultSub.Errorf(message, args...)
}

// Fatal formats the given parts with fmt.Sprint and log them with the Fatal level
func Fatal(parts ...interface{}) {
	DefaultLogger.DefaultSub.Fatal(parts...)
}

// Fatalln formats the given parts with fmt.Sprintln and log them with the Fatal level
func Fatalln(parts ...interface{}) {
	DefaultLogger.DefaultSub.Fatalln(parts...)
}

// Fatalf formats the given message and args with fmt.Sprintf and log them with the Fatal level
func Fatalf(message string, args ...interface{}) {
	DefaultLogger.DefaultSub.Fatalf(message, args...)
}

// Write formats the given parts with fmt.Sprint and log them with the Write level
func (log *Logger) Write(p []byte) (n int, err error) {
	return log.DefaultSub.Write(p)
}

// Log formats the given parts with fmt.Sprint and log them with the Log level
func (log *Logger) Log(level Level, parts ...interface{}) {
	log.DefaultSub.Log(level, parts...)
}

// Logln formats the given parts with fmt.Sprintln and log them with the Log level
func (log *Logger) Logln(level Level, parts ...interface{}) {
	log.DefaultSub.Logln(level, parts...)
}

// Logf formats the given message and args with fmt.Sprintf and log them with the Log level
func (log *Logger) Logf(level Level, message string, args ...interface{}) {
	log.DefaultSub.Logf(level, message, args...)
}

// Debug formats the given parts with fmt.Sprint and log them with the Debug level
func (log *Logger) Debug(parts ...interface{}) {
	log.DefaultSub.Debug(parts...)
}

// Debugln formats the given parts with fmt.Sprintln and log them with the Debug level
func (log *Logger) Debugln(parts ...interface{}) {
	log.DefaultSub.Debugln(parts...)
}

// Debugf formats the given message and args with fmt.Sprintf and log them with the Debug level
func (log *Logger) Debugf(message string, args ...interface{}) {
	log.DefaultSub.Debugf(message, args...)
}

// Info formats the given parts with fmt.Sprint and log them with the Info level
func (log *Logger) Info(parts ...interface{}) {
	log.DefaultSub.Info(parts...)
}

// Infoln formats the given parts with fmt.Sprintln and log them with the Info level
func (log *Logger) Infoln(parts ...interface{}) {
	log.DefaultSub.Infoln(parts...)
}

// Infof formats the given message and args with fmt.Sprintf and log them with the Info level
func (log *Logger) Infof(message string, args ...interface{}) {
	log.DefaultSub.Infof(message, args...)
}

// Warn formats the given parts with fmt.Sprint and log them with the Warn level
func (log *Logger) Warn(parts ...interface{}) {
	log.DefaultSub.Warn(parts...)
}

// Warnln formats the given parts with fmt.Sprintln and log them with the Warn level
func (log *Logger) Warnln(parts ...interface{}) {
	log.DefaultSub.Warnln(parts...)
}

// Warnf formats the given message and args with fmt.Sprintf and log them with the Warn level
func (log *Logger) Warnf(message string, args ...interface{}) {
	log.DefaultSub.Warnf(message, args...)
}

// Error formats the given parts with fmt.Sprint and log them with the Error level
func (log *Logger) Error(parts ...interface{}) {
	log.DefaultSub.Error(parts...)
}

// Errorln formats the given parts with fmt.Sprintln and log them with the Error level
func (log *Logger) Errorln(parts ...interface{}) {
	log.DefaultSub.Errorln(parts...)
}

// Errorf formats the given message and args with fmt.Sprintf and log them with the Error level
func (log *Logger) Errorf(message string, args ...interface{}) {
	log.DefaultSub.Errorf(message, args...)
}

// Fatal formats the given parts with fmt.Sprint and log them with the Fatal level
func (log *Logger) Fatal(parts ...interface{}) {
	log.DefaultSub.Fatal(parts...)
}

// Fatalln formats the given parts with fmt.Sprintln and log them with the Fatal level
func (log *Logger) Fatalln(parts ...interface{}) {
	log.DefaultSub.Fatalln(parts...)
}

// Fatalf formats the given message and args with fmt.Sprintf and log them with the Fatal level
func (log *Logger) Fatalf(message string, args ...interface{}) {
	log.DefaultSub.Fatalf(message, args...)
}

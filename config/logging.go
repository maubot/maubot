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

package config

import (
	"errors"
	"os"
	"path/filepath"
	"strings"
	"text/template"

	"maunium.net/go/maulogger"
)

// LogConfig contains configs for the logger.
type LogConfig struct {
	Directory       string `yaml:"directory"`
	FileNameFormat  string `yaml:"file_name_format"`
	FileDateFormat  string `yaml:"file_date_format"`
	FileMode        uint32 `yaml:"file_mode"`
	TimestampFormat string `yaml:"timestamp_format"`
	RawPrintLevel   string `yaml:"print_level"`
	PrintLevel      int    `yaml:"-"`
}

type umLogConfig LogConfig

func (lc *LogConfig) UnmarshalYAML(unmarshal func(interface{}) error) error {
	err := unmarshal((*umLogConfig)(lc))
	if err != nil {
		return err
	}

	switch strings.ToUpper(lc.RawPrintLevel) {
	case "DEBUG":
		lc.PrintLevel = maulogger.LevelDebug.Severity
	case "INFO":
		lc.PrintLevel = maulogger.LevelInfo.Severity
	case "WARN", "WARNING":
		lc.PrintLevel = maulogger.LevelWarn.Severity
	case "ERR", "ERROR":
		lc.PrintLevel = maulogger.LevelError.Severity
	case "FATAL":
		lc.PrintLevel = maulogger.LevelFatal.Severity
	default:
		return errors.New("invalid print level " + lc.RawPrintLevel)
	}
	return err
}

func (lc *LogConfig) MarshalYAML() (interface{}, error) {
	switch {
	case lc.PrintLevel >= maulogger.LevelFatal.Severity:
		lc.RawPrintLevel = maulogger.LevelFatal.Name
	case lc.PrintLevel >= maulogger.LevelError.Severity:
		lc.RawPrintLevel = maulogger.LevelError.Name
	case lc.PrintLevel >= maulogger.LevelWarn.Severity:
		lc.RawPrintLevel = maulogger.LevelWarn.Name
	case lc.PrintLevel >= maulogger.LevelInfo.Severity:
		lc.RawPrintLevel = maulogger.LevelInfo.Name
	default:
		lc.RawPrintLevel = maulogger.LevelDebug.Name
	}
	return lc, nil
}

// CreateLogConfig creates a basic LogConfig.
func CreateLogConfig() LogConfig {
	return LogConfig{
		Directory:       "./logs",
		FileNameFormat:  "{{.Date}}-{{.Index}}.log",
		TimestampFormat: "Jan _2, 2006 15:04:05",
		FileMode:        0600,
		FileDateFormat:  "2006-01-02",
		PrintLevel:      10,
	}
}

type FileFormatData struct {
	Date string
	Index int
}

// GetFileFormat returns a mauLogger-compatible logger file format based on the data in the struct.
func (lc LogConfig) GetFileFormat() maulogger.LoggerFileFormat {
	os.MkdirAll(lc.Directory, 0700)
	path := filepath.Join(lc.Directory, lc.FileNameFormat)
	tpl, _ := template.New("fileformat").Parse(path)

	return func(now string, i int) string {
		var buf strings.Builder
		tpl.Execute(&buf, FileFormatData{
			Date: now,
			Index: i,
		})
		return buf.String()
	}
}

// Configure configures a mauLogger instance with the data in this struct.
func (lc LogConfig) Configure(log maulogger.Logger) {
	basicLogger := log.(*maulogger.BasicLogger)
	basicLogger.FileFormat = lc.GetFileFormat()
	basicLogger.FileMode = os.FileMode(lc.FileMode)
	basicLogger.FileTimeFormat = lc.FileDateFormat
	basicLogger.TimeFormat = lc.TimestampFormat
	basicLogger.PrintLevel = lc.PrintLevel
}

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
	"maunium.net/go/maulogger"
	"os"
	"fmt"
)

// LogConfig contains configs for the logger.
type LogConfig struct {
	Directory       string `yaml:"directory"`
	FileNameFormat  string `yaml:"file_name_format"`
	FileDateFormat  string `yaml:"file_date_format"`
	FileMode        uint32 `yaml:"file_mode"`
	TimestampFormat string `yaml:"timestamp_format"`
	Debug           bool   `yaml:"print_debug"`
}

// CreateLogConfig creates a basic LogConfig.
func CreateLogConfig() LogConfig {
	return LogConfig{
		Directory:       "./logs",
		FileNameFormat:  "%[1]s-%02[2]d.log",
		TimestampFormat: "Jan _2, 2006 15:04:05",
		FileMode:        0600,
		FileDateFormat:  "2006-01-02",
		Debug:           false,
	}
}

// GetFileFormat returns a mauLogger-compatible logger file format based on the data in the struct.
func (lc LogConfig) GetFileFormat() maulogger.LoggerFileFormat {
	path := lc.FileNameFormat
	if len(lc.Directory) > 0 {
		path = lc.Directory + "/" + path
	}

	return func(now string, i int) string {
		return fmt.Sprintf(path, now, i)
	}
}

// Configure configures a mauLogger instance with the data in this struct.
func (lc LogConfig) Configure(log *maulogger.Logger) {
	log.FileFormat = lc.GetFileFormat()
	log.FileMode = os.FileMode(lc.FileMode)
	log.FileTimeFormat = lc.FileDateFormat
	log.TimeFormat = lc.TimestampFormat
	if lc.Debug {
		log.PrintLevel = maulogger.LevelDebug.Severity
	}
}

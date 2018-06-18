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

package database

import (
	"database/sql"

	log "maunium.net/go/maulogger"
)

type Scannable interface {
	Scan(...interface{}) error
}

type Database struct {
	Type string `yaml:"type"`
	Name string `yaml:"name"`

	MatrixClient *MatrixClientStatic `yaml:"-"`
	Plugin       *PluginStatic       `yaml:"-"`
	CommandSpec  *CommandSpecStatic  `yaml:"-"`

	sql *sql.DB
}

func (db *Database) Connect() (err error) {
	db.sql, err = sql.Open(db.Type, db.Name)
	if err != nil {
		return
	}

	db.MatrixClient = &MatrixClientStatic{db: db, sql: db.sql}
	db.Plugin = &PluginStatic{db: db, sql: db.sql}
	db.CommandSpec = &CommandSpecStatic{db: db, sql: db.sql}

	return nil
}

func (db *Database) CreateTables() {
	log.Debugln("Creating database tables")

	err := db.MatrixClient.CreateTable()
	if err != nil {
		log.Errorln("Failed to create matrix_client table:", err)
	}

	err = db.Plugin.CreateTable()
	if err != nil {
		log.Errorln("Failed to create plugin table:", err)
	}
}

func (db *Database) SQL() *sql.DB {
	return db.sql
}

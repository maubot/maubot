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
	"encoding/json"

	"maubot.xyz"
	log "maunium.net/go/maulogger"
)

type CommandSpec struct {
	db  *Database
	sql *sql.DB

	*maubot.CommandSpec
	Owner  string `json:"owner"`
	Client string `json:"client"`
}

type CommandSpecStatic struct {
	db  *Database
	sql *sql.DB
}

func (css *CommandSpecStatic) CreateTable() error {
	_, err := css.sql.Exec(`CREATE TABLE IF NOT EXISTS command_spec (
		owner  VARCHAR(255),
		client VARCHAR(255),
		spec   TEXT,

		PRIMARY KEY (owner, client),
		FOREIGN KEY (owner) REFERENCES plugin(id)
				ON DELETE CASCADE ON UPDATE CASCADE,
		FOREIGN KEY (client) REFERENCES matrix_client(user_id)
				ON DELETE CASCADE ON UPDATE CASCADE
	)`)
	return err
}

func (css *CommandSpecStatic) Get(owner, client string) *CommandSpec {
	row := css.sql.QueryRow("SELECT * FROM command_spec WHERE owner=? AND client=?", owner, client)
	if row != nil {
		return css.New().Scan(row)
	}
	return nil
}

func (css *CommandSpecStatic) GetOrCreate(owner, client string) (spec *CommandSpec) {
	spec = css.Get(owner, client)
	if spec == nil {
		spec = css.New()
		spec.Owner = owner
		spec.Client = client
		spec.Insert()
	}
	return
}

func (css *CommandSpecStatic) getAllByQuery(query string, args ...interface{}) (specs []*CommandSpec) {
	rows, err := css.sql.Query(query, args...)
	if err != nil || rows == nil {
		return nil
	}
	defer rows.Close()
	for rows.Next() {
		specs = append(specs, css.New().Scan(rows))
	}
	return
}

func (css *CommandSpecStatic) GetAllByOwner(owner string) []*CommandSpec {
	return css.getAllByQuery("SELECT * FROM command_spec WHERE owner=?", owner)
}

func (css *CommandSpecStatic) GetAllByClient(client string) []*CommandSpec {
	return css.getAllByQuery("SELECT * FROM command_spec WHERE client=?", client)
}

func (css *CommandSpecStatic) New() *CommandSpec {
	return &CommandSpec{
		db:  css.db,
		sql: css.sql,
	}
}

func (cs *CommandSpec) Scan(row Scannable) *CommandSpec {
	var spec string
	err := row.Scan(&cs.Owner, &cs.Client, &spec)
	if err != nil {
		log.Fatalln("Database scan failed:", err)
	}
	json.Unmarshal([]byte(spec), &cs.CommandSpec)
	return cs
}

func (cs *CommandSpec) Insert() error {
	data, err := json.Marshal(cs.CommandSpec)
	if err != nil {
		return err
	}
	_, err = cs.sql.Exec("INSERT INTO command_spec (owner, client, spec) VALUES (?, ?, ?)",
		cs.Owner, cs.Client, string(data))
	return err
}

func (cs *CommandSpec) Update() error {
	data, err := json.Marshal(cs.CommandSpec)
	if err != nil {
		return err
	}
	_, err = cs.sql.Exec("UPDATE command_spec SET spec=? WHERE owner=? AND client=?",
		string(data), cs.Owner, cs.Client)
	return err
}

// jesaribot - A simple maubot plugin.
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

type Plugin struct {
	db  *Database
	sql *sql.DB

	ID      string `json:"id"`
	Type    string `json:"type"`
	Enabled bool   `json:"enabled"`
	UserID  string `json:"user_id"`
	//User    *MatrixClient `json:"-"`
}

type PluginStatic struct {
	db  *Database
	sql *sql.DB
}

func (ps *PluginStatic) CreateTable() error {
	_, err := ps.sql.Exec(`CREATE TABLE IF NOT EXISTS plugin (
		id      VARCHAR(255) PRIMARY KEY,
		type    VARCHAR(255) NOT NULL,
		enabled BOOLEAN      NOT NULL,

		user_id VARCHAR(255) NOT NULL,

		FOREIGN KEY (user_id) REFERENCES matrix_client(user_id)
				ON DELETE RESTRICT ON UPDATE CASCADE
	)`)
	return err
}

func (ps *PluginStatic) Get(id string) *Plugin {
	row := ps.sql.QueryRow("SELECT * FROM plugin WHERE id=?", id)
	if row != nil {
		return ps.New().Scan(row)
	}
	return nil
}

func (ps *PluginStatic) GetAll() (plugins []*Plugin) {
	rows, err := ps.sql.Query("SELECT * FROM plugin")
	if err != nil || rows == nil {
		return nil
	}
	defer rows.Close()
	for rows.Next() {
		plugins = append(plugins, ps.New().Scan(rows))
	}
	return
}

func (ps *PluginStatic) New() *Plugin {
	return &Plugin{
		db:  ps.db,
		sql: ps.sql,
	}
}

/*func (p *Plugin) LoadUser() *Plugin {
	p.User = p.db.MatrixClient.Get(p.UserID)
	return p
}*/

func (p *Plugin) Scan(row Scannable) *Plugin {
	err := row.Scan(&p.ID, &p.Type, &p.Enabled, &p.UserID)
	if err != nil {
		log.Fatalln("Database scan failed:", err)
	}
	return p
}

func (p *Plugin) Insert() error {
	_, err := p.sql.Exec("INSERT INTO plugin (id, type, enabled, user_id) VALUES (?, ?, ?, ?)",
		p.ID, p.Type, p.Enabled, p.UserID)
	return err
}

func (p *Plugin) Update() error {
	_, err := p.sql.Exec("UPDATE plugin SET enabled=? WHERE id=?",
		p.Enabled, p.ID)
	return err
}

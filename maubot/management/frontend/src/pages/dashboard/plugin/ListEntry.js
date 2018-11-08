// maubot - A plugin-based Matrix bot system.
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
import React from "react"
import { Link } from "react-router-dom"
import { ReactComponent as ChevronRight } from "../../../res/chevron-right.svg"

const PluginListEntry = ({ plugin }) => (
    <Link className="plugin entry" to={`/plugin/${plugin.id}`}>
        <span className="id">{plugin.id}</span>
        <ChevronRight/>
    </Link>
)

export default PluginListEntry

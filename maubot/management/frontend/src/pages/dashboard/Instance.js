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
import React, { Component } from "react"
import { NavLink } from "react-router-dom"
import { ReactComponent as ChevronRight } from "../../res/chevron-right.svg"

const InstanceListEntry = ({ instance }) => (
    <NavLink className="instance entry" to={`/instance/${instance.id}`}>
        <span className="id">{instance.id}</span>
        <ChevronRight/>
    </NavLink>
)

class Instance extends Component {
    static ListEntry = InstanceListEntry

    render() {
        return <div>{this.props.id}</div>
    }
}

export default Instance

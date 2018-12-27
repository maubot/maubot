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
import { NavLink, Link, Route } from "react-router-dom"
import { ReactComponent as ChevronLeft } from "../../res/chevron-left.svg"
import { ReactComponent as OrderDesc } from "../../res/sort-down.svg"
import { ReactComponent as OrderAsc } from "../../res/sort-up.svg"
import api from "../../api"
import Spinner from "../../components/Spinner"

class InstanceDatabase extends Component {
    constructor(props) {
        super(props)
        this.state = {
            tables: null,
            sortBy: null,
        }
    }

    async componentWillMount() {
        const tables = new Map(Object.entries(await api.getInstanceDatabase(this.props.instanceID)))
        for (const table of tables.values()) {
            table.columns = new Map(Object.entries(table.columns))
            for (const column of table.columns.values()) {
                column.sort = "desc"
            }
        }
        this.setState({ tables })
    }

    toggleSort(column) {
        column.sort = column.sort === "desc" ? "asc" : "desc"
        this.forceUpdate()
    }

    renderTable = ({ match }) => {
        const table = this.state.tables.get(match.params.table)
        console.log(table)
        return <div className="table">
            <table>
                <thead>
                    <tr>
                        {Array.from(table.columns.entries()).map(([name, column]) => (
                            <td key={name}>
                                <span onClick={() => this.toggleSort(column)}>
                                    {name}
                                    {column.sort === "desc" ? <OrderDesc/> : <OrderAsc/>}
                                </span>
                            </td>
                        ))}
                    </tr>
                </thead>
                <tbody>
                </tbody>
            </table>
        </div>
    }

    renderContent() {
        return <>
            <div className="tables">
                {Object.keys(this.state.tables).map(key => (
                    <NavLink key={key} to={`/instance/${this.props.instanceID}/database/${key}`}>
                        {key}
                    </NavLink>
                ))}
            </div>
            <Route path={`/instance/${this.props.instanceID}/database/:table`}
                   render={this.renderTable}/>
        </>
    }

    render() {
        return <div className="instance-database">
            <div className="topbar">
                <Link className="topbar" to={`/instance/${this.props.instanceID}`}>
                    <ChevronLeft/>
                    Back
                </Link>
            </div>
            {this.state.tables
                ? this.renderContent()
                : <Spinner className="maubot-loading"/>}
        </div>
    }
}

export default InstanceDatabase

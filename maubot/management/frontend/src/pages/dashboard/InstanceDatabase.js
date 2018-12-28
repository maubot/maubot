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
import { NavLink, Link, Route, withRouter } from "react-router-dom"
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
            tableContent: null,
        }
        this.sortBy = []
    }

    async componentWillMount() {
        const tables = new Map(Object.entries(await api.getInstanceDatabase(this.props.instanceID)))
        for (const [name, table] of tables) {
            table.name = name
            table.columns = new Map(Object.entries(table.columns))
            for (const [columnName, column] of table.columns) {
                column.name = columnName
                column.sort = null
            }
        }
        this.setState({ tables })
        this.checkLocationTable()
    }

    componentDidUpdate(prevProps) {
        if (this.props.location !== prevProps.location) {
            this.sortBy = []
            this.setState({ tableContent: null })
            this.checkLocationTable()
        }
    }

    checkLocationTable() {
        const prefix = `/instance/${this.props.instanceID}/database/`
        if (this.props.location.pathname.startsWith(prefix)) {
            const table = this.props.location.pathname.substr(prefix.length)
            this.reloadContent(table)
        }
    }

    getSortQuery(table) {
        const sort = []
        for (const column of this.sortBy) {
            sort.push(`order=${column.name}:${column.sort}`)
        }
        return sort
    }

    async reloadContent(name) {
        const table = this.state.tables.get(name)
        const query = this.getSortQuery(table)
        query.push("limit=100")
        this.setState({
            tableContent: await api.getInstanceDatabaseTable(
                this.props.instanceID, table.name, query),
        })
    }

    toggleSort(tableName, column) {
        const index = this.sortBy.indexOf(column)
        if (index >= 0) {
            this.sortBy.splice(index, 1)
        }
        switch (column.sort) {
        default:
            column.sort = "desc"
            this.sortBy.unshift(column)
            break
        case "desc":
            column.sort = "asc"
            this.sortBy.unshift(column)
            break
        case "asc":
            column.sort = null
            break
        }
        this.forceUpdate()
        this.reloadContent(tableName)
    }

    renderTableHead = table => <thead>
        <tr>
            {Array.from(table.columns.entries()).map(([name, column]) => (
                <td key={name}>
                    <span onClick={() => this.toggleSort(table.name, column)}>
                        {name}
                        {column.sort === "desc" ?
                            <OrderDesc/> :
                            column.sort === "asc"
                                ? <OrderAsc/>
                                : null}
                    </span>
                </td>
            ))}
        </tr>
    </thead>

    renderTable = ({ match }) => {
        const table = this.state.tables.get(match.params.table)
        return <div className="table">
            {this.state.tableContent ? (
                <table>
                    {this.renderTableHead(table)}
                    <tbody>
                        {this.state.tableContent.map(row => (
                            <tr key={row}>
                                {row.map((column, index) => (
                                    <td key={index}>
                                        {column}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            ) : <>
                <table>
                    {this.renderTableHead(table)}
                </table>
                <Spinner/>
            </>}

        </div>
    }

    renderContent() {
        return <>
            <div className="tables">
                {Array.from(this.state.tables.keys()).map(key => (
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

export default withRouter(InstanceDatabase)

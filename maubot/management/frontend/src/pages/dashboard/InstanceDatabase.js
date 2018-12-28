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
import { NavLink, Link, withRouter } from "react-router-dom"
import { ReactComponent as ChevronLeft } from "../../res/chevron-left.svg"
import { ReactComponent as OrderDesc } from "../../res/sort-down.svg"
import { ReactComponent as OrderAsc } from "../../res/sort-up.svg"
import api from "../../api"
import Spinner from "../../components/Spinner"

Map.prototype.map = function(func) {
    const res = []
    for (const [key, value] of this) {
        res.push(func(value, key, this))
    }
    return res
}

class InstanceDatabase extends Component {
    constructor(props) {
        super(props)
        this.state = {
            tables: null,
            header: null,
            content: null,
            query: "",
            selectedTable: null,

            error: null,

            prevQuery: null,
            rowCount: null,
            insertedPrimaryKey: null,
        }
        this.order = new Map()
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
            this.order = new Map()
            this.setState({ header: null, content: null })
            this.checkLocationTable()
        }
    }

    checkLocationTable() {
        const prefix = `/instance/${this.props.instanceID}/database/`
        if (this.props.location.pathname.startsWith(prefix)) {
            const table = this.props.location.pathname.substr(prefix.length)
            this.setState({ selectedTable: table })
            this.buildSQLQuery(table)
        }
    }

    getSortQueryParams(table) {
        const order = []
        for (const [column, sort] of Array.from(this.order.entries()).reverse()) {
            order.push(`order=${column}:${sort}`)
        }
        return order
    }

    buildSQLQuery(table = this.state.selectedTable) {
        let query = `SELECT * FROM ${table}`

        if (this.order.size > 0) {
            const order = Array.from(this.order.entries()).reverse()
                .map(([column, sort]) => `${column} ${sort}`)
            query += ` ORDER BY ${order.join(", ")}`
        }

        query += " LIMIT 100"
        this.setState({ query }, this.reloadContent)
    }

    reloadContent = async () => {
        this.setState({ loading: true })
        const res = await api.queryInstanceDatabase(this.props.instanceID, this.state.query)
        this.setState({
            loading: false,
            prevQuery: null,
            rowCount: null,
            insertedPrimaryKey: null,
            error: null,
        })
        if (!res.ok) {
            this.setState({
                error: res.error,
            })
            this.buildSQLQuery()
        } else if (res.rows) {
            this.setState({
                header: res.columns,
                content: res.rows,
            })
        } else {
            this.setState({
                prevQuery: res.query,
                rowCount: res.rowcount,
                insertedPrimaryKey: res.insertedPrimaryKey,
            })
            this.buildSQLQuery()
        }
    }

    toggleSort(column) {
        const oldSort = this.order.get(column) || "auto"
        this.order.delete(column)
        switch (oldSort) {
        case "auto":
            this.order.set(column, "DESC")
            break
        case "DESC":
            this.order.set(column, "ASC")
            break
        case "ASC":
        default:
            break
        }
        this.buildSQLQuery()
    }

    getSortIcon(column) {
        switch (this.order.get(column)) {
        case "DESC":
            return <OrderDesc/>
        case "ASC":
            return <OrderAsc/>
        default:
            return null
        }
    }

    renderTable = () => <div className="table">
        {this.state.header ? (
            <table>
                <thead>
                    <tr>
                        {this.state.header.map(column => (
                            <td key={column}>
                                <span onClick={() => this.toggleSort(column)}>
                                    {column}
                                    {this.getSortIcon(column)}
                                </span>
                            </td>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {this.state.content.map((row, index) => (
                        <tr key={index}>
                            {row.map((column, index) => (
                                <td key={index}>
                                    {column}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        ) : this.state.loading ? <Spinner/> : null}
    </div>

    renderContent() {
        return <>
            <div className="tables">
                {this.state.tables.map((_, tbl) => (
                    <NavLink key={tbl} to={`/instance/${this.props.instanceID}/database/${tbl}`}>
                        {tbl}
                    </NavLink>
                ))}
            </div>
            <div className="query">
                <input type="text" value={this.state.query} name="query"
                       onChange={evt => this.setState({ query: evt.target.value })}/>
                <button type="submit" onClick={this.reloadContent}>Query</button>
            </div>
            {this.state.error && <div className="error">
                {this.state.error}
            </div>}
            {this.state.prevQuery && <div className="prev-query">
                <p>
                    Executed <span className="query">{this.state.prevQuery}</span> -
                    affected <strong>{this.state.rowCount} rows</strong>.
                </p>
                {this.state.insertedPrimaryKey && <p className="inserted-primary-key">
                    Inserted primary key: {this.state.insertedPrimaryKey}
                </p>}
            </div>}
            {this.renderTable()}
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

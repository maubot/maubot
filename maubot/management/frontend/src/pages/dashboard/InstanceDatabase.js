// maubot - A plugin-based Matrix bot system.
// Copyright (C) 2021 Tulir Asokan
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
import { ContextMenu, ContextMenuTrigger, MenuItem } from "react-contextmenu"
import { ReactComponent as ChevronLeft } from "../../res/chevron-left.svg"
import { ReactComponent as OrderDesc } from "../../res/sort-down.svg"
import { ReactComponent as OrderAsc } from "../../res/sort-up.svg"
import api from "../../api"
import Spinner from "../../components/Spinner"

// eslint-disable-next-line no-extend-native
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

    async componentDidMount() {
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

    buildSQLQuery(table = this.state.selectedTable, resetContent = true) {
        let query = `SELECT * FROM "${table}"`

        if (this.order.size > 0) {
            const order = Array.from(this.order.entries()).reverse()
                .map(([column, sort]) => `${column} ${sort}`)
            query += ` ORDER BY ${order.join(", ")}`
        }

        query += " LIMIT 100"
        this.setState({ query }, () => this.reloadContent(resetContent))
    }

    reloadContent = async (resetContent = true) => {
        this.setState({ loading: true })
        const res = await api.queryInstanceDatabase(this.props.instanceID, this.state.query)
        this.setState({ loading: false })
        if (resetContent) {
            this.setState({
                prevQuery: null,
                rowCount: null,
                insertedPrimaryKey: null,
                error: null,
            })
        }
        if (!res.ok) {
            this.setState({
                error: res.error,
            })
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
            this.buildSQLQuery(this.state.selectedTable, false)
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

    getColumnInfo(columnName) {
        const table = this.state.tables.get(this.state.selectedTable)
        if (!table) {
            return null
        }
        const column = table.columns.get(columnName)
        if (!column) {
            return null
        }
        if (column.primary) {
            return <span className="meta">&nbsp;(pk)</span>
        } else if (column.unique) {
            return <span className="meta">&nbsp;(u)</span>
        }
        return null
    }

    getColumnType(columnName) {
        const table = this.state.tables.get(this.state.selectedTable)
        if (!table) {
            return null
        }
        const column = table.columns.get(columnName)
        if (!column) {
            return null
        }
        return column.type
    }

    deleteRow = async (_, data) => {
        const values = this.state.content[data.row]
        const keys = this.state.header
        const condition = []
        for (const [index, key] of Object.entries(keys)) {
            const val = values[index]
            condition.push(`${key}='${this.sqlEscape(val.toString())}'`)
        }
        const query = `DELETE FROM "${this.state.selectedTable}" WHERE ${condition.join(" AND ")}`
        const res = await api.queryInstanceDatabase(this.props.instanceID, query)
        this.setState({
            prevQuery: `DELETE FROM "${this.state.selectedTable}" ...`,
            rowCount: res.rowcount,
        })
        await this.reloadContent(false)
    }

    editCell = async (evt, data) => {
        console.log("Edit", data)
    }

    collectContextMeta = props => ({
        row: props.row,
        col: props.col,
    })

    // eslint-disable-next-line no-control-regex
    sqlEscape = str => str.replace(/[\0\x08\x09\x1a\n\r"'\\%]/g, char => {
        switch (char) {
        case "\0":
            return "\\0"
        case "\x08":
            return "\\b"
        case "\x09":
            return "\\t"
        case "\x1a":
            return "\\z"
        case "\n":
            return "\\n"
        case "\r":
            return "\\r"
        case "\"":
        case "'":
        case "\\":
        case "%":
            return "\\" + char
        default:
            return char
        }
    })

    renderTable = () => <div className="table">
        {this.state.header ? <>
            <table>
                <thead>
                    <tr>
                        {this.state.header.map(column => (
                            <td key={column}>
                                <span onClick={() => this.toggleSort(column)}
                                      title={this.getColumnType(column)}>
                                    <strong>{column}</strong>
                                    {this.getColumnInfo(column)}
                                    {this.getSortIcon(column)}
                                </span>
                            </td>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {this.state.content.map((row, rowIndex) => (
                        <tr key={rowIndex}>
                            {row.map((cell, colIndex) => (
                                <ContextMenuTrigger key={colIndex} id="database_table_menu"
                                                    renderTag="td" row={rowIndex} col={colIndex}
                                                    collect={this.collectContextMeta}>
                                    {cell}
                                </ContextMenuTrigger>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
            <ContextMenu id="database_table_menu">
                <MenuItem onClick={this.deleteRow}>Delete row</MenuItem>
                <MenuItem disabled onClick={this.editCell}>Edit cell</MenuItem>
            </ContextMenu>
        </> : this.state.loading ? <Spinner/> : null}
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

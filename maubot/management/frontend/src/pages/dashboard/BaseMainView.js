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
import { Link } from "react-router-dom"
import api from "../../api"

class BaseMainView extends Component {
    constructor(props) {
        super(props)
        this.state = Object.assign(this.initialState, props.entry)
    }

    UNSAFE_componentWillReceiveProps(nextProps) {
        const newState = Object.assign(this.initialState, nextProps.entry)
        for (const key of this.entryKeys) {
            if (this.props.entry[key] === nextProps.entry[key]) {
                newState[key] = this.state[key]
            }
        }
        this.setState(newState)
    }

    delete = async () => {
        if (!window.confirm(`Are you sure you want to delete ${this.state.id}?`)) {
            return
        }
        this.setState({ deleting: true })
        const resp = await this.deleteFunc(this.state.id)
        if (resp.success) {
            this.props.history.push("/")
            this.props.onDelete()
        } else {
            this.setState({ deleting: false, error: resp.error })
        }
    }

    get entryKeys() {
        return []
    }

    get initialState() {
        return {}
    }

    get hasInstances() {
        return this.state.instances && this.state.instances.length > 0
    }

    get isNew() {
        return !this.props.entry.id
    }

    inputChange = event => {
        if (!event.target.name) {
            return
        }
        this.setState({ [event.target.name]: event.target.value })
    }

    async readFile(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader()
            reader.readAsArrayBuffer(file)
            reader.onload = evt => resolve(evt.target.result)
            reader.onerror = err => reject(err)
        })
    }

    renderInstances = () => !this.isNew && (
        <div className="instances">
            <h3>{this.hasInstances ? "Instances" : "No instances :("}</h3>
            {this.state.instances.map(instance => (
                <Link className="instance" key={instance.id} to={`/instance/${instance.id}`}>
                    {instance.id}
                </Link>
            ))}
        </div>
    )

    renderLogButton = (filter) => !this.isNew && api.getFeatures().log && <div className="buttons">
        <button className="open-log" onClick={() => this.props.openLog(filter)}>View logs</button>
    </div>
}

export default BaseMainView

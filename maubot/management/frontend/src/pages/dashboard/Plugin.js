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
import { NavLink, Link } from "react-router-dom"
import { ReactComponent as ChevronRight } from "../../res/chevron-right.svg"
import { ReactComponent as UploadButton } from "../../res/upload.svg"
import PrefTable, { PrefInput } from "../../components/PreferenceTable"
import Spinner from "../../components/Spinner"
import api from "../../api"

const PluginListEntry = ({ plugin }) => (
    <NavLink className="plugin entry" to={`/plugin/${plugin.id}`}>
        <span className="id">{plugin.id}</span>
        <ChevronRight/>
    </NavLink>
)


class Plugin extends Component {
    static ListEntry = PluginListEntry

    constructor(props) {
        super(props)
        this.state = Object.assign(this.initialState, props.plugin)
    }

    get initialState() {
        return {
            id: "",
            version: "",

            instances: [],

            uploading: false,
            deleting: false,
            error: "",
        }
    }

    componentWillReceiveProps(nextProps) {
        this.setState(Object.assign(this.initialState, nextProps.plugin))
    }

    async readFile(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader()
            reader.readAsArrayBuffer(file)
            reader.onload = evt => resolve(evt.target.result)
            reader.onerror = err => reject(err)
        })
    }
    upload = async event => {
        const file = event.target.files[0]
        this.setState({
            uploadingAvatar: true,
        })
        const data = await this.readFile(file)
        const resp = await api.uploadPlugin(data, this.state.id)
        if (resp.id) {
            if (this.isNew) {
                this.props.history.push(`/plugin/${resp.id}`)
            } else {
                this.setState({ saving: false, error: "" })
            }
            this.props.onChange(resp)
        } else {
            this.setState({ saving: false, error: resp.error })
        }
    }

    delete = async () => {
        if (!window.confirm(`Are you sure you want to delete ${this.state.id}?`)) {
            return
        }
        this.setState({ deleting: true })
        const resp = await api.deletePlugin(this.state.id)
        if (resp.success) {
            this.props.history.push("/")
            this.props.onDelete()
        } else {
            this.setState({ deleting: false, error: resp.error })
        }
    }

    get isNew() {
        return !Boolean(this.props.plugin)
    }

    get hasInstances() {
        return this.state.instances.length > 0
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

    render() {
        return <div className="plugin">
            <div className={`upload-box ${this.state.uploading ? "uploading" : ""}`}>
                <UploadButton className="upload"/>
                <input className="file-selector" type="file" accept="application/zip"
                       onChange={this.upload} disabled={this.state.uploading || this.state.deleting}
                       onDragEnter={evt => evt.target.parentElement.classList.add("drag")}
                       onDragLeave={evt => evt.target.parentElement.classList.remove("drag")}/>
                {this.state.uploading && <Spinner/>}
            </div>
            {!this.isNew && <>
                <PrefTable>
                    <PrefInput rowName="ID" type="text" value={this.state.id} disabled={true}/>
                    <PrefInput rowName="Version" type="text" value={this.state.version}
                               disabled={true}/>
                </PrefTable>
                <div className="buttons">
                    <button className={`delete ${this.hasInstances ? "disabled-bg" : ""}`}
                            onClick={this.delete} disabled={this.loading || this.hasInstances}
                            title={this.hasInstances ? "Can't delete plugin that is in use" : ""}>
                        {this.state.deleting ? <Spinner/> : "Delete"}
                    </button>
                </div>
            </>}
            <div className="error">{this.state.error}</div>
            {!this.isNew && this.renderInstances()}
        </div>
    }
}

export default Plugin

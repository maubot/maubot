// maubot - A plugin-based Matrix bot system.
// Copyright (C) 2019 Tulir Asokan
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
import { NavLink, withRouter } from "react-router-dom"
import { ReactComponent as ChevronRight } from "../../res/chevron-right.svg"
import { ReactComponent as UploadButton } from "../../res/upload.svg"
import PrefTable, { PrefInput } from "../../components/PreferenceTable"
import Spinner from "../../components/Spinner"
import api from "../../api"
import BaseMainView from "./BaseMainView"

const PluginListEntry = ({ entry }) => (
    <NavLink className="plugin entry" to={`/plugin/${entry.id}`}>
        <span className="id">{entry.id}</span>
        <ChevronRight className='chevron'/>
    </NavLink>
)


class Plugin extends BaseMainView {
    static ListEntry = PluginListEntry

    constructor(props) {
        super(props)
        this.deleteFunc = api.deletePlugin
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

    render() {
        return <div className="plugin">
            {!this.isNew && <PrefTable>
                <PrefInput rowName="ID" type="text" value={this.state.id} disabled={true}
                           className="id"/>
                <PrefInput rowName="Version" type="text" value={this.state.version}
                           disabled={true}/>
            </PrefTable>}
            {api.getFeatures().plugin_upload &&
            <div className={`upload-box ${this.state.uploading ? "uploading" : ""}`}>
                <UploadButton className="upload"/>
                <input className="file-selector" type="file" accept="application/zip+mbp"
                       onChange={this.upload} disabled={this.state.uploading || this.state.deleting}
                       onDragEnter={evt => evt.target.parentElement.classList.add("drag")}
                       onDragLeave={evt => evt.target.parentElement.classList.remove("drag")}/>
                {this.state.uploading && <Spinner/>}
            </div>}
            {!this.isNew && <div className="buttons">
                <button className={`delete ${this.hasInstances ? "disabled-bg" : ""}`}
                        onClick={this.delete} disabled={this.loading || this.hasInstances}
                        title={this.hasInstances ? "Can't delete plugin that is in use" : ""}>
                    {this.state.deleting ? <Spinner/> : "Delete"}
                </button>
            </div>}
            {this.renderLogButton("loader.zip")}
            <div className="error">{this.state.error}</div>
            {this.renderInstances()}
        </div>
    }
}

export default withRouter(Plugin)

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
import { Link } from "react-router-dom"
import { ReactComponent as ChevronRight } from "../../res/chevron-right.svg"
import { ReactComponent as UploadButton } from "../../res/upload.svg"
import { PrefTable, PrefSwitch, PrefInput } from "../../components/PreferenceTable"
import Spinner from "../../components/Spinner"
import api from "../../api"

function getAvatarURL(client) {
    if (!client.avatar_url) {
        return ""
    }
    const id = client.avatar_url.substr("mxc://".length)
    return `${client.homeserver}/_matrix/media/r0/download/${id}`
}

const ClientListEntry = ({ client }) => {
    const classes = ["client", "entry"]
    if (!client.enabled) {
        classes.push("disabled")
    } else if (!client.started) {
        classes.push("stopped")
    }
    return (
        <Link className={classes.join(" ")} to={`/client/${client.id}`}>
            <img className="avatar" src={getAvatarURL(client)} alt={client.id.substr(1, 1)}/>
            <span className="displayname">{client.displayname || client.id}</span>
            <ChevronRight/>
        </Link>
    )
}

class Client extends Component {
    static ListEntry = ClientListEntry

    constructor(props) {
        super(props)
        this.state = Object.assign(this.initialState, props.client)
    }

    get initialState() {
        return {
            id: "",
            displayname: "",
            homeserver: "",
            avatar_url: "",
            access_token: "",
            sync: true,
            autojoin: true,
            enabled: true,
            started: false,

            uploadingAvatar: false,
            saving: false,
            startingOrStopping: false,
        }
    }

    componentWillReceiveProps(nextProps) {
        this.setState(Object.assign(this.initialState, nextProps.client))
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

    avatarUpload = async event => {
        const file = event.target.files[0]
        this.setState({
            uploadingAvatar: true,
        })
        const data = await this.readFile(file)
        const resp = await api.uploadAvatar(this.state.id, data, file.type)
        this.setState({
            uploadingAvatar: false,
            avatar_url: resp.content_uri,
        })
    }

    save = async () => {
        this.setState({ saving: true })
        const resp = await api.putClient(this.state)
        if (resp.id) {
            resp.saving = false
            this.setState(resp)
        } else {
            console.error(resp)
        }
    }

    startOrStop = async () => {
        this.setState({ startingOrStopping: true })
        const resp = await api.putClient({
            id: this.state.id,
            started: !this.state.started,
        })
        if (resp.id) {
            resp.startingOrStopping = false
            this.setState(resp)
        } else {
            console.error(resp)
        }
    }

    render() {
        return <div className="client">
            <div className="sidebar">
                <div className={`avatar-container ${this.state.avatar_url ? "" : "no-avatar"}
                        ${this.state.uploadingAvatar ? "uploading" : ""}`}>
                    <img className="avatar" src={getAvatarURL(this.state)} alt="Avatar"/>
                    <UploadButton className="upload"/>
                    <input className="file-selector" type="file" accept="image/png, image/jpeg"
                           onChange={this.avatarUpload} disabled={this.state.uploadingAvatar}/>
                    {this.state.uploadingAvatar && <Spinner/>}
                </div>
                {this.props.client && (<>
                    <div className="started-container">
                        <span className={`started ${this.state.started}`}/>
                        <span className="text">{this.state.started ? "Started" : "Stopped"}</span>
                    </div>
                    <button className="save" onClick={this.startOrStop}
                            disabled={this.state.saving || this.state.startingOrStopping}>
                        {this.state.startingOrStopping ? <Spinner/>
                            : (this.state.started ? "Stop" : "Start")}
                    </button>
                </>)}
            </div>
            <div className="info-container">
                <PrefTable>
                    <PrefInput rowName="User ID" type="text" disabled={!!this.props.client}
                               name={this.props.client ? "" : "id"}
                               value={this.state.id} placeholder="@fancybot:example.com"
                               onChange={this.inputChange}/>
                    <PrefInput rowName="Display name" type="text" name="displayname"
                               value={this.state.displayname} placeholder="My fancy bot"
                               onChange={this.inputChange}/>
                    <PrefInput rowName="Homeserver" type="text" name="homeserver"
                               value={this.state.homeserver} placeholder="https://example.com"
                               onChange={this.inputChange}/>
                    <PrefInput rowName="Access token" type="text" name="access_token"
                               value={this.state.access_token} onChange={this.inputChange}
                               placeholder="MDAxYWxvY2F0aW9uIG1hdHJpeC5sb2NhbAowMDEzaWRlbnRpZmllc"/>
                    <PrefSwitch rowName="Sync" active={this.state.sync}
                                onToggle={sync => this.setState({ sync })}/>
                    <PrefSwitch rowName="Autojoin" active={this.state.autojoin}
                                onToggle={autojoin => this.setState({ autojoin })}/>
                    <PrefSwitch rowName="Enabled" active={this.state.enabled}
                                onToggle={enabled => this.setState({ enabled })}/>
                </PrefTable>

                <button className="save" onClick={this.save}
                        disabled={this.state.saving || this.state.startingOrStopping}>
                    {this.state.saving ? <Spinner/> : "Save"}
                </button>
            </div>
        </div>
    }
}

export default Client

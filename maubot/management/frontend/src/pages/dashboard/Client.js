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
import { PrefTable, PrefSwitch, PrefInput, PrefSelect } from "../../components/PreferenceTable"
import Spinner from "../../components/Spinner"
import api from "../../api"
import BaseMainView from "./BaseMainView"

const ClientListEntry = ({ entry }) => {
    const classes = ["client", "entry"]
    if (!entry.enabled) {
        classes.push("disabled")
    } else if (!entry.started) {
        classes.push("stopped")
    }
    return (
        <NavLink className={classes.join(" ")} to={`/client/${entry.id}`}>
            <img className="avatar" src={api.getAvatarURL(entry)} alt=""/>
            <span className="displayname">{entry.displayname || entry.id}</span>
            <ChevronRight/>
        </NavLink>
    )
}

class Client extends BaseMainView {
    static ListEntry = ClientListEntry

    constructor(props) {
        super(props)
        this.deleteFunc = api.deleteClient
    }

    get entryKeys() {
        return ["id", "displayname", "homeserver", "avatar_url", "access_token", "sync",
            "autojoin", "enabled", "started"]
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

            instances: [],

            uploadingAvatar: false,
            saving: false,
            deleting: false,
            startingOrStopping: false,
            error: "",
        }
    }

    get clientInState() {
        const client = Object.assign({}, this.state)
        delete client.uploadingAvatar
        delete client.saving
        delete client.deleting
        delete client.startingOrStopping
        delete client.error
        delete client.instances
        return client
    }

    get selectedHomeserver() {
        return this.state.homeserver
            ? this.homeserverEntry([this.props.ctx.homeserversByURL[this.state.homeserver],
                this.state.homeserver])
            : {}
    }

    homeserverEntry = ([serverName, serverURL]) => serverURL && {
        id: serverURL,
        value: serverURL,
        label: serverName || serverURL,
    }

    componentWillReceiveProps(nextProps) {
        super.componentWillReceiveProps(nextProps)
        this.updateHomeserverOptions()
    }

    updateHomeserverOptions() {
        this.homeserverOptions = Object.entries(this.props.ctx.homeserversByName).map(this.homeserverEntry)
    }

    isValidHomeserver(value) {
        try {
            return Boolean(new URL(value))
        } catch (err) {
            return false
        }
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
        const resp = await api.putClient(this.clientInState)
        if (resp.id) {
            if (this.isNew) {
                this.props.history.push(`/client/${resp.id}`)
            } else {
                this.setState({ saving: false, error: "" })
            }
            this.props.onChange(resp)
        } else {
            this.setState({ saving: false, error: resp.error })
        }
    }

    startOrStop = async () => {
        this.setState({ startingOrStopping: true })
        const resp = await api.putClient({
            id: this.props.entry.id,
            started: !this.props.entry.started,
        })
        if (resp.id) {
            this.props.onChange(resp)
            this.setState({ startingOrStopping: false, error: "" })
        } else {
            this.setState({ startingOrStopping: false, error: resp.error })
        }
    }

    get loading() {
        return this.state.saving || this.state.startingOrStopping || this.state.deleting
    }

    renderSidebar = () => !this.isNew && (
        <div className="sidebar">
            <div className={`avatar-container ${this.state.avatar_url ? "" : "no-avatar"}
                        ${this.state.uploadingAvatar ? "uploading" : ""}`}>
                <img className="avatar" src={api.getAvatarURL(this.state)} alt="Avatar"/>
                <UploadButton className="upload"/>
                <input className="file-selector" type="file" accept="image/png, image/jpeg"
                       onChange={this.avatarUpload} disabled={this.state.uploadingAvatar}
                       onDragEnter={evt => evt.target.parentElement.classList.add("drag")}
                       onDragLeave={evt => evt.target.parentElement.classList.remove("drag")}/>
                {this.state.uploadingAvatar && <Spinner/>}
            </div>
            <div className="started-container">
                <span className={`started ${this.props.entry.started}
                        ${this.props.entry.enabled ? "" : "disabled"}`}/>
                <span className="text">
                    {this.props.entry.started ? "Started" :
                        (this.props.entry.enabled ? "Stopped" : "Disabled")}
                </span>
            </div>
            {(this.props.entry.started || this.props.entry.enabled) && (
                <button className="save" onClick={this.startOrStop} disabled={this.loading}>
                    {this.state.startingOrStopping ? <Spinner/>
                        : (this.props.entry.started ? "Stop" : "Start")}
                </button>
            )}
        </div>
    )

    renderPreferences = () => (
        <PrefTable>
            <PrefInput rowName="User ID" type="text" disabled={!this.isNew} fullWidth={true}
                       name={this.isNew ? "id" : ""} className="id"
                       value={this.state.id} origValue={this.props.entry.id}
                       placeholder="@fancybot:example.com" onChange={this.inputChange}/>
            <PrefSelect rowName="Homeserver" options={this.homeserverOptions} isSearchable={true}
                        value={this.selectedHomeserver} origValue={this.props.entry.homeserver}
                        onChange={({ id }) => this.setState({ homeserver: id })}
                        creatable={true} isValidNewOption={this.isValidHomeserver}/>
            <PrefInput rowName="Access token" type="text" name="access_token"
                       value={this.state.access_token} origValue={this.props.entry.access_token}
                       placeholder="MDAxYWxvY2F0aW9uIG1hdHJpeC5sb2NhbAowMDEzaWRlbnRpZmllc"
                       onChange={this.inputChange}/>
            <PrefInput rowName="Display name" type="text" name="displayname"
                       value={this.state.displayname} origValue={this.props.entry.displayname}
                       placeholder="My fancy bot" onChange={this.inputChange}/>
            <PrefInput rowName="Avatar URL" type="text" name="avatar_url"
                       value={this.state.avatar_url} origValue={this.props.entry.avatar_url}
                       placeholder="mxc://example.com/mbmwyoTvPhEQPiCskcUsppko"
                       onChange={this.inputChange}/>
            <PrefSwitch rowName="Sync"
                        active={this.state.sync} origActive={this.props.entry.sync}
                        onToggle={sync => this.setState({ sync })}/>
            <PrefSwitch rowName="Autojoin"
                        active={this.state.autojoin} origActive={this.props.entry.autojoin}
                        onToggle={autojoin => this.setState({ autojoin })}/>
            <PrefSwitch rowName="Enabled"
                        active={this.state.enabled} origActive={this.props.entry.enabled}
                        onToggle={enabled => this.setState({
                            enabled,
                            started: enabled && this.state.started,
                        })}/>
        </PrefTable>
    )

    renderPrefButtons = () => <>
        <div className="buttons">
            {!this.isNew && (
                <button className={`delete ${this.hasInstances ? "disabled-bg" : ""}`}
                        onClick={this.delete} disabled={this.loading || this.hasInstances}
                        title={this.hasInstances ? "Can't delete client that is in use" : ""}>
                    {this.state.deleting ? <Spinner/> : "Delete"}
                </button>
            )}
            <button className="save" onClick={this.save} disabled={this.loading}>
                {this.state.saving ? <Spinner/> : (this.isNew ? "Create" : "Save")}
            </button>
        </div>
        {this.renderLogButton(this.state.id)}
        <div className="error">{this.state.error}</div>
    </>

    render() {
        return <>
            <div className="client">
                {this.renderSidebar()}
                <div className="info">
                    {this.renderPreferences()}
                    {this.renderPrefButtons()}
                    {this.renderInstances()}
                </div>
            </div>
        </>
    }
}

export default withRouter(Client)

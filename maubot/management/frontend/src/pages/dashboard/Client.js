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
import React from "react"
import { NavLink, withRouter } from "react-router-dom"
import { ReactComponent as ChevronRight } from "../../res/chevron-right.svg"
import { ReactComponent as UploadButton } from "../../res/upload.svg"
import { ReactComponent as NoAvatarIcon } from "../../res/bot.svg"
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
    const avatarMXC = entry.avatar_url === "disable"
        ? entry.remote_avatar_url
        : entry.avatar_url
    const avatarURL = avatarMXC && api.getAvatarURL({
        id: entry.id,
        avatar_url: avatarMXC,
    })
    const displayname = (
        entry.displayname === "disable"
            ? entry.remote_displayname
            : entry.displayname
    ) || entry.id
    return (
        <NavLink className={classes.join(" ")} to={`/client/${entry.id}`}>
            {avatarURL
                ? <img className='avatar' src={avatarURL} alt=""/>
                : <NoAvatarIcon className='avatar'/>}
            <span className="displayname">{displayname}</span>
            <ChevronRight className='chevron'/>
        </NavLink>
    )
}

class Client extends BaseMainView {
    static ListEntry = ClientListEntry

    constructor(props) {
        super(props)
        this.deleteFunc = api.deleteClient
        this.homeserverOptions = []
    }

    get entryKeys() {
        return ["id", "displayname", "homeserver", "avatar_url", "access_token", "device_id",
                "sync", "autojoin", "online", "enabled", "started"]
    }

    get initialState() {
        return {
            id: "",
            displayname: "",
            homeserver: "",
            avatar_url: "",
            access_token: "",
            device_id: "",
            fingerprint: null,
            sync: true,
            autojoin: true,
            enabled: true,
            online: true,
            started: false,

            instances: [],

            uploadingAvatar: false,
            saving: false,
            deleting: false,
            startingOrStopping: false,
            clearingCache: false,
            error: "",
        }
    }

    get clientInState() {
        const client = Object.assign({}, this.state)
        delete client.uploadingAvatar
        delete client.saving
        delete client.deleting
        delete client.startingOrStopping
        delete client.clearingCache
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

    componentDidUpdate(prevProps) {
        this.updateHomeserverOptions()
    }

    updateHomeserverOptions() {
        this.homeserverOptions = Object
            .entries(this.props.ctx.homeserversByName)
            .map(this.homeserverEntry)
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

    clearCache = async () => {
        this.setState({ clearingCache: true })
        const resp = await api.clearClientCache(this.props.entry.id)
        if (resp.success) {
            this.setState({ clearingCache: false, error: "" })
        } else {
            this.setState({ clearingCache: false, error: resp.error })
        }
    }

    get loading() {
        return this.state.saving || this.state.startingOrStopping
            || this.clearingCache || this.state.deleting
    }

    renderStartedContainer = () => {
        let text
        if (this.props.entry.started) {
            if (this.props.entry.sync_ok) {
                text = "Started"
            } else {
                text = "Erroring"
            }
        } else if (this.props.entry.enabled) {
            text = "Stopped"
        } else {
            text = "Disabled"
        }
        return <div className="started-container">
            <span className={`started ${this.props.entry.started}
                             ${this.props.entry.sync_ok ? "sync_ok" : "sync_error"}
                             ${this.props.entry.enabled ? "" : "disabled"}`}/>
            <span className="text">{text}</span>
        </div>
    }

    get avatarMXC() {
        if (this.state.avatar_url === "disable") {
            return this.props.entry.remote_avatar_url
        } else if (!this.state.avatar_url?.startsWith("mxc://")) {
            return null
        }
        return this.state.avatar_url
    }

    get avatarURL() {
        return api.getAvatarURL({
            id: this.state.id,
            avatar_url: this.avatarMXC,
        })
    }

    renderSidebar = () => !this.isNew && (
        <div className="sidebar">
            <div className={`avatar-container ${this.avatarMXC ? "" : "no-avatar"}
                        ${this.state.uploadingAvatar ? "uploading" : ""}`}>
                {this.avatarMXC && <img className="avatar" src={this.avatarURL} alt="Avatar"/>}
                <UploadButton className="upload"/>
                <input className="file-selector" type="file" accept="image/png, image/jpeg"
                       onChange={this.avatarUpload} disabled={this.state.uploadingAvatar}
                       onDragEnter={evt => evt.target.parentElement.classList.add("drag")}
                       onDragLeave={evt => evt.target.parentElement.classList.remove("drag")}/>
                {this.state.uploadingAvatar && <Spinner/>}
            </div>
            {this.renderStartedContainer()}
            {(this.props.entry.started || this.props.entry.enabled) && <>
                <button className="save" onClick={this.startOrStop} disabled={this.loading}>
                    {this.state.startingOrStopping ? <Spinner/>
                        : (this.props.entry.started ? "Stop" : "Start")}
                </button>
                <button className="clearcache" onClick={this.clearCache} disabled={this.loading}>
                    {this.state.clearingCache ? <Spinner/> : "Clear cache"}
                </button>
            </>}
        </div>
    )

    renderPreferences = () => (
        <PrefTable>
            <PrefInput rowName="User ID" type="text" disabled={!this.isNew} fullWidth={true}
                       name={this.isNew ? "id" : ""} className="id"
                       value={this.state.id} origValue={this.props.entry.id}
                       placeholder="@fancybot:example.com" onChange={this.inputChange}/>
            {api.getFeatures().client_auth ? (
                <PrefSelect rowName="Homeserver" options={this.homeserverOptions} fullWidth={true}
                            isSearchable={true} value={this.selectedHomeserver}
                            origValue={this.props.entry.homeserver}
                            onChange={({ value }) => this.setState({ homeserver: value })}
                            creatable={true} isValidNewOption={this.isValidHomeserver}/>
            ) : (
                <PrefInput rowName="Homeserver" type="text" name="homeserver" fullWidth={true}
                           value={this.state.homeserver} origValue={this.props.entry.homeserver}
                           placeholder="https://example.com" onChange={this.inputChange}/>
            )}
            <PrefInput rowName="Access token" type="text" name="access_token"
                       value={this.state.access_token} origValue={this.props.entry.access_token}
                       placeholder="syt_bWF1Ym90_tUleVHiGyLKwXLaAMqlm_0afdcq"
                       onChange={this.inputChange}/>
            <PrefInput rowName="Device ID" type="text" name="device_id"
                       value={this.state.device_id} origValue={this.props.entry.device_id}
                       placeholder="maubot_F00BAR12" onChange={this.inputChange}/>
            {this.props.entry.fingerprint && <PrefInput
                rowName="E2EE device fingerprint" type="text" disabled={true} fullWidth={true}
                value={this.props.entry.fingerprint} className="fingerprint"
            />}
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
            <PrefSwitch rowName="Online"
                        active={this.state.online} origActive={this.props.entry.online}
                        onToggle={online => this.setState({ online })} />
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

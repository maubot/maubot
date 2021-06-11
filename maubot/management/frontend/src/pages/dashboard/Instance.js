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
import { Link, NavLink, Route, Switch, withRouter } from "react-router-dom"
import AceEditor from "react-ace"
import "ace-builds/src-noconflict/mode-yaml"
import "ace-builds/src-noconflict/theme-github"
import { ReactComponent as ChevronRight } from "../../res/chevron-right.svg"
import { ReactComponent as NoAvatarIcon } from "../../res/bot.svg"
import PrefTable, { PrefInput, PrefSelect, PrefSwitch } from "../../components/PreferenceTable"
import api from "../../api"
import Spinner from "../../components/Spinner"
import BaseMainView from "./BaseMainView"
import InstanceDatabase from "./InstanceDatabase"

const InstanceListEntry = ({ entry }) => (
    <NavLink className="instance entry" to={`/instance/${entry.id}`}>
        <span className="id">{entry.id}</span>
        <ChevronRight className='chevron'/>
    </NavLink>
)

class Instance extends BaseMainView {
    static ListEntry = InstanceListEntry

    constructor(props) {
        super(props)
        this.deleteFunc = api.deleteInstance
        this.updateClientOptions()
    }

    get entryKeys() {
        return ["id", "primary_user", "enabled", "started", "type", "config"]
    }

    get initialState() {
        return {
            id: "",
            primary_user: "",
            enabled: true,
            started: true,
            type: "",
            config: "",

            saving: false,
            deleting: false,
            error: "",
        }
    }

    get instanceInState() {
        const instance = Object.assign({}, this.state)
        delete instance.saving
        delete instance.deleting
        delete instance.error
        return instance
    }

    componentDidUpdate(prevProps) {
        this.updateClientOptions()
    }

    getAvatarMXC(client) {
        return client.avatar_url === "disable" ? client.remote_avatar_url : client.avatar_url
    }

    getAvatarURL(client) {
        return api.getAvatarURL({
            id: client.id,
            avatar_url: this.getAvatarMXC(client),
        })
    }

    clientSelectEntry = client => client && {
        id: client.id,
        value: client.id,
        label: (
            <div className="select-client">
                {this.getAvatarMXC(client)
                    ? <img className="avatar" src={this.getAvatarURL(client)} alt=""/>
                    : <NoAvatarIcon className='avatar'/>}
                <span className="displayname">{
                    (client.displayname === "disable"
                        ? client.remote_displayname
                        : client.displayname
                    ) || client.id
                }</span>
            </div>
        ),
    }

    updateClientOptions() {
        this.clientOptions = Object.values(this.props.ctx.clients).map(this.clientSelectEntry)
    }

    save = async () => {
        this.setState({ saving: true })
        const resp = await api.putInstance(this.instanceInState, this.props.entry
            ? this.props.entry.id : undefined)
        if (resp.id) {
            if (this.isNew) {
                this.props.history.push(`/instance/${resp.id}`)
            } else {
                if (resp.id !== this.props.entry.id) {
                    this.props.history.replace(`/instance/${resp.id}`)
                }
                this.setState({ saving: false, error: "" })
            }
            this.props.onChange(resp)
        } else {
            this.setState({ saving: false, error: resp.error })
        }
    }

    get selectedClientEntry() {
        return this.state.primary_user
            ? this.clientSelectEntry(this.props.ctx.clients[this.state.primary_user])
            : {}
    }

    get selectedPluginEntry() {
        return {
            id: this.state.type,
            value: this.state.type,
            label: this.state.type,
        }
    }

    get typeOptions() {
        return Object.values(this.props.ctx.plugins).map(plugin => plugin && {
            id: plugin.id,
            value: plugin.id,
            label: plugin.id,
        })
    }

    get loading() {
        return this.state.deleting || this.state.saving
    }

    get isValid() {
        return this.state.id && this.state.primary_user && this.state.type
    }

    render() {
        return <Switch>
            <Route path="/instance/:id/database" render={this.renderDatabase}/>
            <Route render={this.renderMain}/>
        </Switch>
    }

    renderDatabase = () => <InstanceDatabase instanceID={this.props.entry.id}/>

    renderMain = () => <div className="instance">
        <PrefTable>
            <PrefInput rowName="ID" type="text" name="id" value={this.state.id}
                       placeholder="fancybotinstance" onChange={this.inputChange}
                       disabled={!this.isNew} fullWidth={true} className="id"/>
            <PrefSwitch rowName="Enabled"
                        active={this.state.enabled} origActive={this.props.entry.enabled}
                        onToggle={enabled => this.setState({ enabled })}/>
            <PrefSwitch rowName="Running"
                        active={this.state.started} origActive={this.props.entry.started}
                        onToggle={started => this.setState({ started })}/>
            {api.getFeatures().client ? (
                <PrefSelect rowName="Primary user" options={this.clientOptions}
                            isSearchable={false} value={this.selectedClientEntry}
                            origValue={this.props.entry.primary_user}
                            onChange={({ id }) => this.setState({ primary_user: id })}/>
            ) : (
                <PrefInput rowName="Primary user" type="text" name="primary_user"
                           value={this.state.primary_user} placeholder="@user:example.com"
                           onChange={this.inputChange}/>
            )}
            {api.getFeatures().plugin ? (
                <PrefSelect rowName="Type" options={this.typeOptions} isSearchable={false}
                            value={this.selectedPluginEntry} origValue={this.props.entry.type}
                            onChange={({ id }) => this.setState({ type: id })}/>
            ) : (
                <PrefInput rowName="Type" type="text" name="type" value={this.state.type}
                           placeholder="xyz.maubot.example" onChange={this.inputChange}/>
            )}
        </PrefTable>
        {!this.isNew && Boolean(this.props.entry.base_config) &&
        <AceEditor mode="yaml" theme="github" onChange={config => this.setState({ config })}
                   name="config" value={this.state.config}
                   editorProps={{
                       fontSize: "10pt",
                       $blockScrolling: true,
                   }}/>}
        <div className="buttons">
            {!this.isNew && (
                <button className="delete" onClick={this.delete} disabled={this.loading}>
                    {this.state.deleting ? <Spinner/> : "Delete"}
                </button>
            )}
            <button className={`save ${this.isValid ? "" : "disabled-bg"}`}
                    onClick={this.save} disabled={this.loading || !this.isValid}>
                {this.state.saving ? <Spinner/> : (this.isNew ? "Create" : "Save")}
            </button>
        </div>
        {!this.isNew && <div className="buttons">
            {this.props.entry.database && (
                <Link className="button open-database"
                      to={`/instance/${this.state.id}/database`}>
                    View database
                </Link>
            )}
            {api.getFeatures().log &&
            <button className="open-log"
                    onClick={() => this.props.openLog(`instance.${this.state.id}`)}>
                View logs
            </button>}
        </div>}
        <div className="error">{this.state.error}</div>
    </div>
}

export default withRouter(Instance)

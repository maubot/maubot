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
import React from "react"
import { NavLink, withRouter } from "react-router-dom"
import AceEditor from "react-ace"
import "brace/mode/yaml"
import "brace/theme/github"
import { ReactComponent as ChevronRight } from "../../res/chevron-right.svg"
import PrefTable, { PrefInput, PrefSelect, PrefSwitch } from "../../components/PreferenceTable"
import api from "../../api"
import Spinner from "../../components/Spinner"
import BaseMainView from "./BaseMainView"

const InstanceListEntry = ({ entry }) => (
    <NavLink className="instance entry" to={`/instance/${entry.id}`}>
        <span className="id">{entry.id}</span>
        <ChevronRight/>
    </NavLink>
)

class Instance extends BaseMainView {
    static ListEntry = InstanceListEntry

    constructor(props) {
        super(props)
        this.deleteFunc = api.deleteInstance
        this.updateClientOptions()
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

    componentWillReceiveProps(nextProps) {
        super.componentWillReceiveProps(nextProps)
        this.updateClientOptions()
    }

    clientSelectEntry = client => client && {
        id: client.id,
        value: client.id,
        label: (
            <div className="select-client">
                <img className="avatar" src={api.getAvatarURL(client.id)} alt=""/>
                <span className="displayname">{client.displayname || client.id}</span>
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
        return <div className="instance">
            <PrefTable>
                <PrefInput rowName="ID" type="text" name="id" value={this.state.id}
                           placeholder="fancybotinstance" onChange={this.inputChange}
                           disabled={!this.isNew} fullWidth={true} className="id"/>
                <PrefSwitch rowName="Enabled" active={this.state.enabled}
                            onToggle={enabled => this.setState({ enabled })}/>
                <PrefSwitch rowName="Running" active={this.state.started}
                            onToggle={started => this.setState({ started })}/>
                <PrefSelect rowName="Primary user" options={this.clientOptions}
                            isSearchable={false} value={this.selectedClientEntry}
                            onChange={({ id }) => this.setState({ primary_user: id })}/>
                <PrefSelect rowName="Type" options={this.typeOptions} isSearchable={false}
                            value={this.selectedPluginEntry}
                            onChange={({ id }) => this.setState({ type: id })}/>
            </PrefTable>
            <AceEditor mode="yaml" theme="github" onChange={config => this.setState({ config })}
                       name="config" value={this.state.config}
                       editorProps={{
                           fontSize: "10pt",
                           $blockScrolling: true,
                       }}/>
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
            <div className="error">{this.state.error}</div>
            {this.renderLog()}
        </div>
    }
}

export default withRouter(Instance)

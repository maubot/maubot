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
import { Route, Switch, Link } from "react-router-dom"
import api from "../../api"
import { ReactComponent as Plus } from "../../res/plus.svg"
import Instance from "./Instance"
import Client from "./Client"
import Plugin from "./Plugin"

class Dashboard extends Component {
    constructor(props) {
        super(props)
        this.state = {
            instances: {},
            clients: {},
            plugins: {},
        }
        global.maubot = this
    }

    async componentWillMount() {
        const [instanceList, clientList, pluginList] = await Promise.all([
            api.getInstances(), api.getClients(), api.getPlugins()])
        const instances = {}
        for (const instance of instanceList) {
            instances[instance.id] = instance
        }
        const clients = {}
        for (const client of clientList) {
            clients[client.id] = client
        }
        const plugins = {}
        for (const plugin of pluginList) {
            plugins[plugin.id] = plugin
        }
        this.setState({ instances, clients, plugins })
    }

    renderList(field, type) {
        return Object.values(this.state[field + "s"]).map(entry =>
            React.createElement(type, { key: entry.id, [field]: entry }))
    }

    delete(stateField, id) {
        const data = Object.assign({}, this.state[stateField])
        delete data[id]
        this.setState({ [stateField]: data })
    }

    add(stateField, entry, oldID = undefined) {
        const data = Object.assign({}, this.state[stateField])
        if (oldID && oldID !== entry.id) {
            delete data[oldID]
        }
        data[entry.id] = entry
        this.setState({ [stateField]: data })
    }

    renderView(field, type, id) {
        const stateField = field + "s"
        const entry = this.state[stateField][id]
        if (!entry) {
            return "Not found :("
        }
        return React.createElement(type, {
            [field]: entry,
            onDelete: () => this.delete(stateField, id),
            onChange: newEntry => this.add(stateField, newEntry, id),
            ctx: this.state,
        })
    }

    render() {
        return <div className="dashboard">
            <Link to="/" className="title">
                <img src="/favicon.png" alt=""/>
                Maubot Manager
            </Link>

            <div className="user">
                <span>{localStorage.username}</span>
            </div>
            <nav className="sidebar">
                <div className="instances list">
                    <div className="title">
                        <h2>Instances</h2>
                        <Link to="/new/instance"><Plus/></Link>
                    </div>
                    {this.renderList("instance", Instance.ListEntry)}
                </div>
                <div className="clients list">
                    <div className="title">
                        <h2>Clients</h2>
                        <Link to="/new/client"><Plus/></Link>
                    </div>
                    {this.renderList("client", Client.ListEntry)}
                </div>
                <div className="plugins list">
                    <div className="title">
                        <h2>Plugins</h2>
                        <Link to="/new/plugin"><Plus/></Link>
                    </div>
                    {this.renderList("plugin", Plugin.ListEntry)}
                </div>
            </nav>
            <main className="view">
                <Switch>
                    <Route path="/" exact render={() => "Hello, World!"}/>
                    <Route path="/new/instance" render={() =>
                        <Instance onChange={newEntry => this.add("instances", newEntry)}
                                  ctx={this.state}/>}/>
                    <Route path="/new/client" render={() => <Client
                        onChange={newEntry => this.add("clients", newEntry)}/>}/>
                    <Route path="/new/plugin" render={() => <Plugin
                        onChange={newEntry => this.add("plugins", newEntry)}/>}/>
                    <Route path="/instance/:id" render={({ match }) =>
                        this.renderView("instance", Instance, match.params.id)}/>
                    <Route path="/client/:id" render={({ match }) =>
                        this.renderView("client", Client, match.params.id)}/>
                    <Route path="/plugin/:id" render={({ match }) =>
                        this.renderView("plugin", Plugin, match.params.id)}/>
                    <Route render={() => "Not found :("}/>
                </Switch>
            </main>
        </div>
    }
}

export default Dashboard

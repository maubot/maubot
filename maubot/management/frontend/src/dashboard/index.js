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
import api from "../api"
import { ReactComponent as Plus } from "../res/plus.svg"
import InstanceListEntry from "./instance/ListEntry"
import InstanceView from "./instance/View"
import ClientListEntry from "./client/ListEntry"
import ClientView from "./client/View"
import PluginListEntry from "./plugin/ListEntry"
import PluginView from "./plugin/View"

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

    renderView(field, type, id) {
        const entry = this.state[field + "s"][id]
        if (!entry) {
            return "Not found :("
        }
        return React.createElement(type, entry)
    }

    render() {
        return <div className="dashboard">
            <Link to="/" className="title">
                <img src="/favicon.png" alt=""/>
                Maubot Manager
            </Link>
            <div className="topbar">
                {localStorage.username}
            </div>
            <nav className="sidebar">
                <div className="instances list">
                    <div className="title">
                        <h2>Instances</h2>
                        <Link to="/new/instance"><Plus/></Link>
                    </div>
                    {this.renderList("instance", InstanceListEntry)}
                </div>
                <div className="clients list">
                    <div className="title">
                        <h2>Clients</h2>
                        <Link to="/new/client"><Plus/></Link>
                    </div>
                    {this.renderList("client", ClientListEntry)}
                </div>
                <div className="plugins list">
                    <div className="title">
                        <h2>Plugins</h2>
                        <Link to="/new/plugin"><Plus/></Link>
                    </div>
                    {this.renderList("plugin", PluginListEntry)}
                </div>
            </nav>
            <main className="dashboard">
                <Switch>
                    <Route path="/" exact render={() => "Hello, World!"}/>
                    <Route path="/new/instance" render={() => <InstanceView/>}/>
                    <Route path="/new/client" render={() => <ClientView/>}/>
                    <Route path="/new/plugin" render={() => <PluginView/>}/>
                    <Route path="/instance/:id" render={({ match }) =>
                        this.renderView("instance", InstanceView, match.params.id)}/>
                    <Route path="/client/:id" render={({ match }) =>
                        this.renderView("client", ClientView, match.params.id)}/>
                    <Route path="/plugin/:id" render={({ match }) =>
                        this.renderView("plugin", PluginView, match.params.id)}/>
                    <Route render={() => "Not found :("}/>
                </Switch>
            </main>
        </div>
    }
}

export default Dashboard

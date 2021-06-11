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
import { HashRouter as Router, Switch } from "react-router-dom"
import PrivateRoute from "../components/PrivateRoute"
import Spinner from "../components/Spinner"
import api from "../api"
import Dashboard from "./dashboard"
import Login from "./Login"

class Main extends Component {
    constructor(props) {
        super(props)
        this.state = {
            pinged: false,
            authed: false,
        }
    }

    async componentDidMount() {
        await this.getBasePath()
        if (localStorage.accessToken) {
            await this.ping()
        } else {
            await api.remoteGetFeatures()
        }
        this.setState({ pinged: true })
    }

    async getBasePath() {
        try {
            const resp = await fetch(process.env.PUBLIC_URL + "/paths.json", {
                headers: { "Content-Type": "application/json" },
            })
            const apiPathJson = await resp.json()
            const apiPath = apiPathJson.api_path
            api.setBasePath(`${apiPath}`)
        } catch (err) {
            console.error("Failed to get API path:", err)
        }
    }


    async ping() {
        try {
            const username = await api.ping()
            if (username) {
                localStorage.username = username
                this.setState({ authed: true })
            } else {
                delete localStorage.accessToken
            }
        } catch (err) {
            console.error(err)
        }
    }

    login = async (token) => {
        localStorage.accessToken = token
        await this.ping()
    }

    render() {
        if (!this.state.pinged) {
            return <Spinner className="maubot-loading"/>
        }
        return <Router>
            <div className={`maubot-wrapper ${this.state.authed ? "authenticated" : ""}`}>
                <Switch>
                    <PrivateRoute path="/login" render={() => <Login onLogin={this.login}/>}
                                  authed={!this.state.authed} to="/"/>
                    <PrivateRoute path="/" component={Dashboard} authed={this.state.authed}/>
                </Switch>
            </div>
        </Router>
    }
}

export default Main

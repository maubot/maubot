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
import { BrowserRouter as Router, Switch } from "react-router-dom"
import PrivateRoute from "./components/PrivateRoute"
import Dashboard from "./dashboard"
import Login from "./Login"
import Spinner from "./components/Spinner"
import api from "./api"

class MaubotRouter extends Component {
    constructor(props) {
        super(props)
        this.state = {
            pinged: false,
            authed: false,
        }
    }

    async componentWillMount() {
        if (localStorage.accessToken) {
            await this.ping()
        }
        this.setState({ pinged: true })
    }

    async ping() {
        try {
            const username = await api.ping()
            if (username) {
                localStorage.username = username
                this.setState({ authed: true })
            } else {
                localStorage.accessToken = undefined
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

export default MaubotRouter

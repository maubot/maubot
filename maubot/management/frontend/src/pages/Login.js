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
import React, { Component } from "react"
import Spinner from "../components/Spinner"
import api from "../api"

class Login extends Component {
    constructor(props, context) {
        super(props, context)
        this.state = {
            username: "",
            password: "",
            loading: false,
            error: "",
        }
    }

    inputChanged = event => this.setState({ [event.target.name]: event.target.value })

    login = async evt => {
        evt.preventDefault()
        this.setState({ loading: true })
        const resp = await api.login(this.state.username, this.state.password)
        if (resp.token) {
            await this.props.onLogin(resp.token)
        } else if (resp.error) {
            this.setState({ error: resp.error, loading: false })
        } else {
            this.setState({ error: "Unknown error", loading: false })
            console.log("Unknown error:", resp)
        }
    }

    render() {
        if (!api.getFeatures().login) {
            return <div className="login-wrapper">
                <div className="login errored">
                    <h1>Maubot Manager</h1>
                    <div className="error">Login has been disabled in the maubot config.</div>
                </div>
            </div>
        }
        return <div className="login-wrapper">
            <form className={`login ${this.state.error && "errored"}`} onSubmit={this.login}>
                <h1>Maubot Manager</h1>
                <input type="text" placeholder="Username" value={this.state.username}
                       name="username" onChange={this.inputChanged}/>
                <input type="password" placeholder="Password" value={this.state.password}
                       name="password" onChange={this.inputChanged}/>
                <button onClick={this.login} type="submit">
                    {this.state.loading ? <Spinner/> : "Log in"}
                </button>
                {this.state.error && <div className="error">{this.state.error}</div>}
            </form>
        </div>
    }
}

export default Login

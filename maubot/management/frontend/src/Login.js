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

class Login extends Component {
    constructor(props, context) {
        super(props, context)
        this.state = {
            username: "",
            password: "",
        }
    }

    inputChanged = event => this.setState({ [event.target.name]: event.target.value })

    login = () => {

    }

    render() {
        return <div className="login-wrapper">
            <div className="login">
                <h1 className="title">Maubot Manager</h1>
                <input type="text" placeholder="Username" value={this.state.username}
                       name="username" onChange={this.inputChanged}/>
                <input type="password" placeholder="Password" value={this.state.password}
                       name="password" onChange={this.inputChanged}/>
                <button onClick={this.login}>Log in</button>
            </div>
        </div>
    }
}

export default Login

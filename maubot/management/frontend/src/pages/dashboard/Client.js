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
import { Link } from "react-router-dom"
import Switch from "../../components/Switch"
import { ReactComponent as ChevronRight } from "../../res/chevron-right.svg"
import { ReactComponent as UploadButton } from "../../res/upload.svg"

function getAvatarURL(client) {
    const id = client.avatar_url.substr("mxc://".length)
    return `${client.homeserver}/_matrix/media/r0/download/${id}`
}

const ClientListEntry = ({ client }) => {
    const classes = ["client", "entry"]
    if (!client.enabled) {
        classes.push("disabled")
    } else if (!client.started) {
        classes.push("stopped")
    }
    return (
        <Link className={classes.join(" ")} to={`/client/${client.id}`}>
            <img className="avatar" src={getAvatarURL(client)} alt={client.id.substr(1, 1)}/>
            <span className="displayname">{client.displayname || client.id}</span>
            <ChevronRight/>
        </Link>
    )
}

class Client extends Component {
    static ListEntry = ClientListEntry

    constructor(props) {
        super(props)
        this.state = props
    }

    componentWillReceiveProps(nextProps) {
        this.setState(nextProps)
    }

    inputChange = event => {
        this.setState({ [event.target.name]: event.target.value })
    }

    render() {
        return <div className="client">
            <div className="avatar-container">
                <img className="avatar" src={getAvatarURL(this.state)} alt="Avatar"/>
                <UploadButton className="upload"/>
            </div>
            <div className="info-container">
                <div className="row">
                    <div className="key">User ID</div>
                    <div className="value">
                        <input type="text" disabled value={this.props.id}
                               onChange={this.inputChange}/>
                    </div>
                </div>
                <div className="row">
                    <div className="key">Display name</div>
                    <div className="value">
                        <input type="text" name="displayname" value={this.state.displayname}
                               onChange={this.inputChange}/>
                    </div>
                </div>
                <div className="row">
                    <div className="key">Homeserver</div>
                    <div className="value">
                        <input type="text" name="homeserver" value={this.state.homeserver}
                               onChange={this.inputChange}/>
                    </div>
                </div>
                <div className="row">
                    <div className="key">Access token</div>
                    <div className="value">
                        <input type="text" name="access_token" value={this.state.access_token}
                               onChange={this.inputChange}/>
                    </div>
                </div>
                <div className="row">
                    <div className="key">Sync</div>
                    <div className="value">
                        <Switch active={this.state.sync}
                                onToggle={sync => this.setState({ sync })}/>
                    </div>
                </div>
                <div className="row">
                    <div className="key">Enabled</div>
                    <div className="value">
                        <Switch active={this.state.enabled}
                                onToggle={enabled => this.setState({ enabled })}/>
                    </div>
                </div>
            </div>

        </div>
    }
}

export default Client

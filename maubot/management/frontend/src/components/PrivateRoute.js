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
import React from "react"
import { Route, Redirect } from "react-router-dom"

const PrivateRoute = ({ component, render, authed, to = "/login", ...args }) => (
    <Route
        {...args}
        render={(props) => authed === true
            ? (component ? React.createElement(component, props) : render())
            : <Redirect to={{ pathname: to }}/>}
    />
)

export default PrivateRoute

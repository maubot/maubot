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
import Switch from "./Switch"

export const PrefTable = ({ children, wrapperClass }) => {
    if (wrapperClass) {
        return (
            <div className={wrapperClass}>
                <div className="preference-table">
                    {children}
                </div>
            </div>
        )
    }
    return (
        <div className="preference-table">
            {children}
        </div>
    )
}

export const PrefRow = ({ name, children }) => (
    <div className="row">
        <div className="key">{name}</div>
        <div className="value">{children}</div>
    </div>
)

export const PrefInput = ({ rowName, ...args }) => (
    <PrefRow name={rowName}>
        <input {...args}/>
    </PrefRow>
)

export const PrefSwitch = ({ rowName, ...args }) => (
    <PrefRow name={rowName}>
        <Switch {...args}/>
    </PrefRow>
)

export default PrefTable

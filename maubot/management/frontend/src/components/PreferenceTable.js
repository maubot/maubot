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
import React from "react"
import Select from "react-select"
import CreatableSelect from "react-select/creatable"
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

export const PrefRow =
    ({ name, fullWidth = false, labelFor = undefined, changed = false, children }) => (
        <div className={`entry ${fullWidth ? "full-width" : ""} ${changed ? "changed" : ""}`}>
            <label htmlFor={labelFor}>{name}</label>
            <div className="value">{children}</div>
        </div>
    )

export const PrefInput = ({ rowName, value, origValue, fullWidth = false, ...args }) => (
    <PrefRow name={rowName} fullWidth={fullWidth} labelFor={rowName}
             changed={origValue !== undefined && value !== origValue}>
        <input {...args} value={value} id={rowName}/>
    </PrefRow>
)

export const PrefSwitch = ({ rowName, active, origActive, fullWidth = false, ...args }) => (
    <PrefRow name={rowName} fullWidth={fullWidth} labelFor={rowName}
             changed={origActive !== undefined && active !== origActive}>
        <Switch {...args} active={active} id={rowName}/>
    </PrefRow>
)

export const PrefSelect = ({
    rowName, value, origValue, fullWidth = false, creatable = false, ...args
}) => (
    <PrefRow name={rowName} fullWidth={fullWidth} labelFor={rowName}
             changed={origValue !== undefined && value.id !== origValue}>
        {creatable
            ? <CreatableSelect className="select" {...args} id={rowName} value={value}/>
            : <Select className="select" {...args} id={rowName} value={value}/>}
    </PrefRow>
)

export default PrefTable

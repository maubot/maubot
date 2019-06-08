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
import React, { Component, createContext } from "react"

const rem = 16

class Modal extends Component {
    static Context = createContext(null)

    constructor(props) {
        super(props)
        this.state = {
            open: false,
        }
        this.wrapper = { clientWidth: 9001 }
    }

    open = () => this.setState({ open: true })
    close = () => this.setState({ open: false })
    isOpen = () => this.state.open

    render() {
        return this.state.open && (
            <div className="modal-wrapper-wrapper" ref={ref => this.wrapper = ref}
                 onClick={() => this.wrapper.clientWidth > 45 * rem && this.close()}>
                <div className="modal-wrapper" onClick={evt => evt.stopPropagation()}>
                    <button className="close" onClick={this.close}>Close</button>
                    <div className="modal">
                        <Modal.Context.Provider value={this}>
                            {this.props.children}
                        </Modal.Context.Provider>
                    </div>
                </div>
            </div>
        )
    }
}

export default Modal

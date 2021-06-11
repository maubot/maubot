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
import React, { PureComponent } from "react"
import { Link } from "react-router-dom"
import JSONTree from "react-json-tree"
import api from "../../api"
import Modal from "./Modal"

class LogEntry extends PureComponent {
    static contextType = Modal.Context

    renderName() {
        const line = this.props.line
        if (line.nameLink) {
            const modal = this.context
            return (
                <Link to={line.nameLink} onClick={modal.close}>
                    {line.name}
                </Link>
            )
        }
        return line.name
    }

    renderContent() {
        if (this.props.line.matrix_http_request) {
            const req = this.props.line.matrix_http_request

            return <>
                {req.method} {req.path}
                <div className="content">
                    {Object.entries(req.content || {}).length > 0
                    && <JSONTree data={{ content: req.content }} hideRoot={true}/>}
                </div>
            </>
        }
        return this.props.line.msg
    }

    onClickOpen(path, line) {
        return () => {
            if (api.debugOpenFileEnabled()) {
                api.debugOpenFile(path, line)
            }
            return false
        }
    }

    renderTimeTitle() {
        return this.props.line.time.toDateString()
    }

    renderTime() {
        return <a className="time" title={this.renderTimeTitle()}
                  href={`file:///${this.props.line.pathname}:${this.props.line.lineno}`}
                  onClick={this.onClickOpen(this.props.line.pathname, this.props.line.lineno)}>
            {this.props.line.time.toLocaleTimeString("en-GB")}
        </a>
    }

    renderLevelName() {
        return <span className="level">
            {this.props.line.levelname}
        </span>
    }

    get unfocused() {
        return this.props.focus && this.props.line.name !== this.props.focus
            ? "unfocused"
            : ""
    }

    renderRow(content) {
        return (
            <div className={`row ${this.props.line.levelname.toLowerCase()} ${this.unfocused}`}>
                {this.renderTime()}
                {this.renderLevelName()}
                <span className="logger">{this.renderName()}</span>
                <span className="text">{content}</span>
            </div>
        )
    }

    renderExceptionInfo() {
        if (!api.debugOpenFileEnabled()) {
            return this.props.line.exc_info
        }
        const fileLinks = []
        let str = this.props.line.exc_info.replace(
            /File "(.+)", line ([0-9]+), in (.+)/g,
            (_, file, line, method) => {
                fileLinks.push(
                    <a href={`file:///${file}:${line}`} onClick={this.onClickOpen(file, line)}>
                        File "{file}", line {line}, in {method}
                    </a>,
                )
                return "||EDGE||"
            })
        fileLinks.reverse()

        const result = []
        let key = 0
        for (const part of str.split("||EDGE||")) {
            result.push(<React.Fragment key={key++}>
                {part}
                {fileLinks.pop()}
            </React.Fragment>)
        }
        return result
    }

    render() {
        return <>
            {this.renderRow(this.renderContent())}
            {this.props.line.exc_info && this.renderRow(this.renderExceptionInfo())}
        </>
    }
}

class Log extends PureComponent {
    constructor(props) {
        super(props)

        this.linesRef = React.createRef()
        this.linesBottomRef = React.createRef()
    }

    getSnapshotBeforeUpdate() {
        if (this.linesRef.current && this.linesBottomRef.current) {
            return Log.isVisible(this.linesRef.current, this.linesBottomRef.current)
        }
        return false
    }


    componentDidUpdate(_1, _2, wasVisible) {
        if (wasVisible) {
            Log.scrollParentToChild(this.linesRef.current, this.linesBottomRef.current)
        }
    }

    componentDidMount() {
        if (this.linesRef.current && this.linesBottomRef.current) {
            Log.scrollParentToChild(this.linesRef.current, this.linesBottomRef.current)
        }
    }

    static scrollParentToChild(parent, child) {
        const parentRect = parent.getBoundingClientRect()
        const childRect = child.getBoundingClientRect()

        if (!Log.isVisible(parent, child)) {
            parent.scrollBy({ top: (childRect.top + parent.scrollTop) - parentRect.top })
        }
    }

    static isVisible(parent, child) {
        const parentRect = parent.getBoundingClientRect()
        const childRect = child.getBoundingClientRect()
        return (childRect.top >= parentRect.top)
            && (childRect.top <= parentRect.top + parent.clientHeight)
    }

    render() {
        return (
            <div className="log" ref={this.linesRef}>
                <div className="lines">
                    {this.props.lines.map(data => <LogEntry key={data.id} line={data}
                                                            focus={this.props.focus}/>)}
                </div>
                <div ref={this.linesBottomRef}/>
            </div>
        )
    }
}

export default Log

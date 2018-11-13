import React, { Component } from "react"
import { Link } from "react-router-dom"
import Log from "./Log"

class BaseMainView extends Component {
    constructor(props) {
        super(props)
        this.state = Object.assign(this.initialState, props.entry)
    }

    componentWillReceiveProps(nextProps) {
        this.setState(Object.assign(this.initialState, nextProps.entry))
    }

    delete = async () => {
        if (!window.confirm(`Are you sure you want to delete ${this.state.id}?`)) {
            return
        }
        this.setState({ deleting: true })
        const resp = await this.deleteFunc(this.state.id)
        if (resp.success) {
            this.props.history.push("/")
            this.props.onDelete()
        } else {
            this.setState({ deleting: false, error: resp.error })
        }
    }

    get initialState() {
        throw Error("Not implemented")
    }

    get hasInstances() {
        return this.state.instances && this.state.instances.length > 0
    }

    get isNew() {
        return !this.props.entry
    }

    inputChange = event => {
        if (!event.target.name) {
            return
        }
        this.setState({ [event.target.name]: event.target.value })
    }

    async readFile(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader()
            reader.readAsArrayBuffer(file)
            reader.onload = evt => resolve(evt.target.result)
            reader.onerror = err => reject(err)
        })
    }

    renderInstances = () => !this.isNew && (
        <div className="instances">
            <h3>{this.hasInstances ? "Instances" : "No instances :("}</h3>
            {this.state.instances.map(instance => (
                <Link className="instance" key={instance.id} to={`/instance/${instance.id}`}>
                    {instance.id}
                </Link>
            ))}
        </div>
    )

    renderLog = () => !this.isNew && <Log showName={false} lines={this.props.log}/>
}

export default BaseMainView

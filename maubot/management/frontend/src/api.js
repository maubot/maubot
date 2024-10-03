// maubot - A plugin-based Matrix bot system.
// Copyright (C) 2022 Tulir Asokan
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

let BASE_PATH = "/_matrix/maubot/v1"

export function setBasePath(basePath) {
    BASE_PATH = basePath
}

function getHeaders(contentType = "application/json") {
    return {
        "Content-Type": contentType,
        "Authorization": `Bearer ${localStorage.accessToken}`,
    }
}

async function defaultDelete(type, id) {
    const resp = await fetch(`${BASE_PATH}/${type}/${id}`, {
        headers: getHeaders(),
        method: "DELETE",
    })
    if (resp.status === 204) {
        return {
            "success": true,
        }
    }
    return await resp.json()
}

async function defaultPut(type, entry, id = undefined, suffix = undefined) {
    const resp = await fetch(`${BASE_PATH}/${type}/${id || entry.id}${suffix || ""}`, {
        headers: getHeaders(),
        body: JSON.stringify(entry),
        method: "PUT",
    })
    return await resp.json()
}

async function defaultGet(path) {
    const resp = await fetch(`${BASE_PATH}${path}`, { headers: getHeaders() })
    return await resp.json()
}

export async function login(username, password) {
    const resp = await fetch(`${BASE_PATH}/auth/login`, {
        method: "POST",
        body: JSON.stringify({
            username,
            password,
        }),
    })
    return await resp.json()
}

let features = null

export async function ping() {
    const response = await fetch(`${BASE_PATH}/auth/ping`, {
        method: "POST",
        headers: getHeaders(),
    })
    const json = await response.json()
    if (json.username) {
        features = json.features
        return json.username
    } else if (json.errcode === "auth_token_missing" || json.errcode === "auth_token_invalid") {
        if (!features) {
            await remoteGetFeatures()
        }
        return null
    }
    throw json
}

export const remoteGetFeatures = async () => {
    features = await defaultGet("/features")
}

export const getFeatures = () => features

export async function openLogSocket() {
    let protocol = window.location.protocol === "https:" ? "wss:" : "ws:"
    const url = `${protocol}//${window.location.host}${BASE_PATH}/logs`
    const wrapper = {
        socket: null,
        connected: false,
        authenticated: false,
        onLog: data => undefined,
        onHistory: history => undefined,
        fails: -1,
    }
    const openHandler = () => {
        wrapper.socket.send(localStorage.accessToken)
        wrapper.connected = true
    }
    const messageHandler = evt => {
        // TODO use logs
        const data = JSON.parse(evt.data)
        if (data.auth_success !== undefined) {
            if (data.auth_success) {
                console.info("Websocket connection authentication successful")
                wrapper.authenticated = true
                wrapper.fails = -1
            } else {
                console.info("Websocket connection authentication failed")
            }
        } else if (data.history) {
            wrapper.onHistory(data.history)
        } else {
            wrapper.onLog(data)
        }
    }
    const closeHandler = evt => {
        if (evt) {
            if (evt.code === 4000) {
                console.error("Websocket connection failed: access token invalid or not provided")
            } else if (evt.code === 1012) {
                console.info("Websocket connection closed: server is restarting")
            }
        }
        wrapper.connected = false
        wrapper.socket = null
        wrapper.fails++
        const SECOND = 1000
        setTimeout(() => {
            wrapper.socket = new WebSocket(url)
            wrapper.socket.onopen = openHandler
            wrapper.socket.onmessage = messageHandler
            wrapper.socket.onclose = closeHandler
        }, Math.min(wrapper.fails * 5 * SECOND, 30 * SECOND))
    }

    closeHandler()

    return wrapper
}

let _debugOpenFileEnabled = undefined
export const debugOpenFileEnabled = () => _debugOpenFileEnabled
export const updateDebugOpenFileEnabled = async () => {
    const resp = await defaultGet("/debug/open")
    _debugOpenFileEnabled = resp["enabled"] || false
}

export async function debugOpenFile(path, line) {
    const resp = await fetch(`${BASE_PATH}/debug/open`, {
        headers: getHeaders(),
        body: JSON.stringify({ path, line }),
        method: "POST",
    })
    return await resp.json()
}

export const getInstances = () => defaultGet("/instances")
export const getInstance = id => defaultGet(`/instance/${id}`)
export const putInstance = (instance, id) => defaultPut("instance", instance, id)
export const deleteInstance = id => defaultDelete("instance", id)

export const getInstanceDatabase = id => defaultGet(`/instance/${id}/database`)
export const queryInstanceDatabase = async (id, query) => {
    const resp = await fetch(`${BASE_PATH}/instance/${id}/database/query`, {
        headers: getHeaders(),
        body: JSON.stringify({ query }),
        method: "POST",
    })
    return await resp.json()
}

export const getPlugins = () => defaultGet("/plugins")
export const getPlugin = id => defaultGet(`/plugin/${id}`)
export const deletePlugin = id => defaultDelete("plugin", id)

export async function uploadPlugin(data, id) {
    let resp
    if (id) {
        resp = await fetch(`${BASE_PATH}/plugin/${id}`, {
            headers: getHeaders("application/zip"),
            body: data,
            method: "PUT",
        })
    } else {
        resp = await fetch(`${BASE_PATH}/plugins/upload`, {
            headers: getHeaders("application/zip"),
            body: data,
            method: "POST",
        })
    }
    return await resp.json()
}

export const getClients = () => defaultGet("/clients")
export const getClient = id => defaultGet(`/clients/${id}`)

export async function uploadAvatar(id, data, mime) {
    const resp = await fetch(`${BASE_PATH}/proxy/${id}/_matrix/media/v3/upload`, {
        headers: getHeaders(mime),
        body: data,
        method: "POST",
    })
    return await resp.json()
}

export function getAvatarURL({ id, avatar_url }) {
    if (!avatar_url?.startsWith("mxc://")) {
        return null
    }
    avatar_url = avatar_url.substring("mxc://".length)
    return `${BASE_PATH}/proxy/${id}/_matrix/client/v1/media/download/${avatar_url}?access_token=${
        localStorage.accessToken}`
}

export const putClient = client => defaultPut("client", client)
export const deleteClient = id => defaultDelete("client", id)

export async function clearClientCache(id) {
    const resp = await fetch(`${BASE_PATH}/client/${id}/clearcache`, {
        headers: getHeaders(),
        method: "POST",
    })
    return await resp.json()
}

export const getClientAuthServers = () => defaultGet("/client/auth/servers")

export async function doClientAuth(server, type, username, password) {
    const resp = await fetch(`${BASE_PATH}/client/auth/${server}/${type}`, {
        headers: getHeaders(),
        body: JSON.stringify({ username, password }),
        method: "POST",
    })
    return await resp.json()
}

// eslint-disable-next-line import/no-anonymous-default-export
export default {
    login, ping, setBasePath, getFeatures, remoteGetFeatures,
    openLogSocket,
    debugOpenFile, debugOpenFileEnabled, updateDebugOpenFileEnabled,
    getInstances, getInstance, putInstance, deleteInstance,
    getInstanceDatabase, queryInstanceDatabase,
    getPlugins, getPlugin, uploadPlugin, deletePlugin,
    getClients, getClient, uploadAvatar, getAvatarURL, putClient, deleteClient, clearClientCache,
    getClientAuthServers, doClientAuth,
}

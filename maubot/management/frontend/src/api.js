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

const BASE_PATH = "/_matrix/maubot/v1"

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

function getHeaders(contentType = "application/json") {
    return {
        "Content-Type": contentType,
        "Authorization": `Bearer ${localStorage.accessToken}`,
    }
}

export async function ping() {
    const response = await fetch(`${BASE_PATH}/auth/ping`, {
        method: "POST",
        headers: getHeaders(),
    })
    const json = await response.json()
    if (json.username) {
        return json.username
    } else if (json.errcode === "auth_token_missing" || json.errcode === "auth_token_invalid") {
        return null
    }
    throw json
}

export async function getInstances() {
    const resp = await fetch(`${BASE_PATH}/instances`, { headers: getHeaders() })
    return await resp.json()
}

export async function getInstance(id) {
    const resp = await fetch(`${BASE_PATH}/instance/${id}`, { headers: getHeaders() })
    return await resp.json()
}

export async function getPlugins() {
    const resp = await fetch(`${BASE_PATH}/plugins`, { headers: getHeaders() })
    return await resp.json()
}

export async function getPlugin(id) {
    const resp = await fetch(`${BASE_PATH}/plugin/${id}`, { headers: getHeaders() })
    return await resp.json()
}

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

export async function getClients() {
    const resp = await fetch(`${BASE_PATH}/clients`, { headers: getHeaders() })
    return await resp.json()
}

export async function getClient(id) {
    const resp = await fetch(`${BASE_PATH}/client/${id}`, { headers: getHeaders() })
    return await resp.json()
}

export async function uploadAvatar(id, data, mime) {
    const resp = await fetch(`${BASE_PATH}/client/${id}/avatar`, {
        headers: getHeaders(mime),
        body: data,
        method: "POST",
    })
    return await resp.json()
}

export async function putClient(client) {
    const resp = await fetch(`${BASE_PATH}/client/${client.id}`, {
        headers: getHeaders(),
        body: JSON.stringify(client),
        method: "PUT",
    })
    return await resp.json()
}

export default {
    login, ping,
    getInstances, getInstance,
    getPlugins, getPlugin, uploadPlugin,
    getClients, getClient, uploadAvatar, putClient,
}

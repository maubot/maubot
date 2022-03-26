# maubot - A plugin-based Matrix bot system.
# Copyright (C) 2022 Tulir Asokan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from __future__ import annotations

from http import HTTPStatus

from aiohttp import web
from asyncpg import PostgresError
from sqlalchemy.exc import IntegrityError, OperationalError
import aiosqlite


class _Response:
    @property
    def body_not_json(self) -> web.Response:
        return web.json_response(
            {
                "error": "Request body is not JSON",
                "errcode": "body_not_json",
            },
            status=HTTPStatus.BAD_REQUEST,
        )

    @property
    def plugin_type_required(self) -> web.Response:
        return web.json_response(
            {
                "error": "Plugin type is required when creating plugin instances",
                "errcode": "plugin_type_required",
            },
            status=HTTPStatus.BAD_REQUEST,
        )

    @property
    def primary_user_required(self) -> web.Response:
        return web.json_response(
            {
                "error": "Primary user is required when creating plugin instances",
                "errcode": "primary_user_required",
            },
            status=HTTPStatus.BAD_REQUEST,
        )

    @property
    def bad_client_access_token(self) -> web.Response:
        return web.json_response(
            {
                "error": "Invalid access token",
                "errcode": "bad_client_access_token",
            },
            status=HTTPStatus.BAD_REQUEST,
        )

    @property
    def bad_client_access_details(self) -> web.Response:
        return web.json_response(
            {
                "error": "Invalid homeserver or access token",
                "errcode": "bad_client_access_details",
            },
            status=HTTPStatus.BAD_REQUEST,
        )

    @property
    def bad_client_connection_details(self) -> web.Response:
        return web.json_response(
            {
                "error": "Could not connect to homeserver",
                "errcode": "bad_client_connection_details",
            },
            status=HTTPStatus.BAD_REQUEST,
        )

    def mxid_mismatch(self, found: str) -> web.Response:
        return web.json_response(
            {
                "error": (
                    "The Matrix user ID of the client and the user ID of the access token don't "
                    f"match. Access token is for user {found}"
                ),
                "errcode": "mxid_mismatch",
            },
            status=HTTPStatus.BAD_REQUEST,
        )

    def device_id_mismatch(self, found: str) -> web.Response:
        return web.json_response(
            {
                "error": (
                    "The Matrix device ID of the client and the device ID of the access token "
                    f"don't match. Access token is for device {found}"
                ),
                "errcode": "mxid_mismatch",
            },
            status=HTTPStatus.BAD_REQUEST,
        )

    @property
    def pid_mismatch(self) -> web.Response:
        return web.json_response(
            {
                "error": "The ID in the path does not match the ID of the uploaded plugin",
                "errcode": "pid_mismatch",
            },
            status=HTTPStatus.BAD_REQUEST,
        )

    @property
    def username_or_password_missing(self) -> web.Response:
        return web.json_response(
            {
                "error": "Username or password missing",
                "errcode": "username_or_password_missing",
            },
            status=HTTPStatus.BAD_REQUEST,
        )

    @property
    def query_missing(self) -> web.Response:
        return web.json_response(
            {
                "error": "Query missing",
                "errcode": "query_missing",
            },
            status=HTTPStatus.BAD_REQUEST,
        )

    @staticmethod
    def sql_error(error: PostgresError | aiosqlite.Error, query: str) -> web.Response:
        return web.json_response(
            {
                "ok": False,
                "query": query,
                "error": str(error),
                "errcode": "sql_error",
            },
            status=HTTPStatus.BAD_REQUEST,
        )

    @staticmethod
    def sql_operational_error(error: OperationalError, query: str) -> web.Response:
        return web.json_response(
            {
                "ok": False,
                "query": query,
                "error": str(error.orig),
                "full_error": str(error),
                "errcode": "sql_operational_error",
            },
            status=HTTPStatus.BAD_REQUEST,
        )

    @staticmethod
    def sql_integrity_error(error: IntegrityError, query: str) -> web.Response:
        return web.json_response(
            {
                "ok": False,
                "query": query,
                "error": str(error.orig),
                "full_error": str(error),
                "errcode": "sql_integrity_error",
            },
            status=HTTPStatus.BAD_REQUEST,
        )

    @property
    def bad_auth(self) -> web.Response:
        return web.json_response(
            {
                "error": "Invalid username or password",
                "errcode": "invalid_auth",
            },
            status=HTTPStatus.UNAUTHORIZED,
        )

    @property
    def no_token(self) -> web.Response:
        return web.json_response(
            {
                "error": "Authorization token missing",
                "errcode": "auth_token_missing",
            },
            status=HTTPStatus.UNAUTHORIZED,
        )

    @property
    def invalid_token(self) -> web.Response:
        return web.json_response(
            {
                "error": "Invalid authorization token",
                "errcode": "auth_token_invalid",
            },
            status=HTTPStatus.UNAUTHORIZED,
        )

    @property
    def plugin_not_found(self) -> web.Response:
        return web.json_response(
            {
                "error": "Plugin not found",
                "errcode": "plugin_not_found",
            },
            status=HTTPStatus.NOT_FOUND,
        )

    @property
    def client_not_found(self) -> web.Response:
        return web.json_response(
            {
                "error": "Client not found",
                "errcode": "client_not_found",
            },
            status=HTTPStatus.NOT_FOUND,
        )

    @property
    def primary_user_not_found(self) -> web.Response:
        return web.json_response(
            {
                "error": "Client for given primary user not found",
                "errcode": "primary_user_not_found",
            },
            status=HTTPStatus.NOT_FOUND,
        )

    @property
    def instance_not_found(self) -> web.Response:
        return web.json_response(
            {
                "error": "Plugin instance not found",
                "errcode": "instance_not_found",
            },
            status=HTTPStatus.NOT_FOUND,
        )

    @property
    def plugin_type_not_found(self) -> web.Response:
        return web.json_response(
            {
                "error": "Given plugin type not found",
                "errcode": "plugin_type_not_found",
            },
            status=HTTPStatus.NOT_FOUND,
        )

    @property
    def path_not_found(self) -> web.Response:
        return web.json_response(
            {
                "error": "Resource not found",
                "errcode": "resource_not_found",
            },
            status=HTTPStatus.NOT_FOUND,
        )

    @property
    def server_not_found(self) -> web.Response:
        return web.json_response(
            {
                "error": "Registration target server not found",
                "errcode": "server_not_found",
            },
            status=HTTPStatus.NOT_FOUND,
        )

    @property
    def registration_secret_not_found(self) -> web.Response:
        return web.json_response(
            {
                "error": "Config does not have a registration secret for that server",
                "errcode": "registration_secret_not_found",
            },
            status=HTTPStatus.NOT_FOUND,
        )

    @property
    def registration_no_sso(self) -> web.Response:
        return web.json_response(
            {
                "error": "The register operation is only for registering with a password",
                "errcode": "registration_no_sso",
            },
            status=HTTPStatus.BAD_REQUEST,
        )

    @property
    def sso_not_supported(self) -> web.Response:
        return web.json_response(
            {
                "error": "That server does not seem to support single sign-on",
                "errcode": "sso_not_supported",
            },
            status=HTTPStatus.FORBIDDEN,
        )

    @property
    def plugin_has_no_database(self) -> web.Response:
        return web.json_response(
            {
                "error": "Given plugin does not have a database",
                "errcode": "plugin_has_no_database",
            }
        )

    @property
    def unsupported_plugin_database(self) -> web.Response:
        return web.json_response(
            {
                "error": "The database type is not supported by this API",
                "errcode": "unsupported_plugin_database",
            }
        )

    @property
    def table_not_found(self) -> web.Response:
        return web.json_response(
            {
                "error": "Given table not found in plugin database",
                "errcode": "table_not_found",
            }
        )

    @property
    def method_not_allowed(self) -> web.Response:
        return web.json_response(
            {
                "error": "Method not allowed",
                "errcode": "method_not_allowed",
            },
            status=HTTPStatus.METHOD_NOT_ALLOWED,
        )

    @property
    def user_exists(self) -> web.Response:
        return web.json_response(
            {
                "error": "There is already a client with the user ID of that token",
                "errcode": "user_exists",
            },
            status=HTTPStatus.CONFLICT,
        )

    @property
    def plugin_exists(self) -> web.Response:
        return web.json_response(
            {
                "error": "A plugin with the same ID as the uploaded plugin already exists",
                "errcode": "plugin_exists",
            },
            status=HTTPStatus.CONFLICT,
        )

    @property
    def plugin_in_use(self) -> web.Response:
        return web.json_response(
            {
                "error": "Plugin instances of this type still exist",
                "errcode": "plugin_in_use",
            },
            status=HTTPStatus.PRECONDITION_FAILED,
        )

    @property
    def client_in_use(self) -> web.Response:
        return web.json_response(
            {
                "error": "Plugin instances with this client as their primary user still exist",
                "errcode": "client_in_use",
            },
            status=HTTPStatus.PRECONDITION_FAILED,
        )

    @staticmethod
    def plugin_import_error(error: str, stacktrace: str) -> web.Response:
        return web.json_response(
            {
                "error": error,
                "stacktrace": stacktrace,
                "errcode": "plugin_invalid",
            },
            status=HTTPStatus.BAD_REQUEST,
        )

    @staticmethod
    def plugin_reload_error(error: str, stacktrace: str) -> web.Response:
        return web.json_response(
            {
                "error": error,
                "stacktrace": stacktrace,
                "errcode": "plugin_reload_fail",
            },
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    @property
    def internal_server_error(self) -> web.Response:
        return web.json_response(
            {
                "error": "Internal server error",
                "errcode": "internal_server_error",
            },
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    @property
    def invalid_server(self) -> web.Response:
        return web.json_response(
            {
                "error": "Invalid registration server object in maubot configuration",
                "errcode": "invalid_server",
            },
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    @property
    def unsupported_plugin_loader(self) -> web.Response:
        return web.json_response(
            {
                "error": "Existing plugin with same ID uses unsupported plugin loader",
                "errcode": "unsupported_plugin_loader",
            },
            status=HTTPStatus.BAD_REQUEST,
        )

    @property
    def not_implemented(self) -> web.Response:
        return web.json_response(
            {
                "error": "Not implemented",
                "errcode": "not_implemented",
            },
            status=HTTPStatus.NOT_IMPLEMENTED,
        )

    @property
    def ok(self) -> web.Response:
        return web.json_response(
            {"success": True},
            status=HTTPStatus.OK,
        )

    @property
    def deleted(self) -> web.Response:
        return web.Response(status=HTTPStatus.NO_CONTENT)

    @staticmethod
    def found(data: dict) -> web.Response:
        return web.json_response(data, status=HTTPStatus.OK)

    @staticmethod
    def updated(data: dict, is_login: bool = False) -> web.Response:
        return web.json_response(data, status=HTTPStatus.ACCEPTED if is_login else HTTPStatus.OK)

    def logged_in(self, token: str) -> web.Response:
        return self.found({"token": token})

    def pong(self, user: str, features: dict) -> web.Response:
        return self.found({"username": user, "features": features})

    @staticmethod
    def created(data: dict) -> web.Response:
        return web.json_response(data, status=HTTPStatus.CREATED)


resp = _Response()

# v0.5.1 (2025-01-03)

* Updated Docker image to Alpine 3.21.
* Updated media upload/download endpoints in management frontend
  (thanks to [@domrim] in [#253]).
* Fixed plugin web app base path not including a trailing slash
  (thanks to [@jkhsjdhjs] in [#240]).
* Changed markdown parsing to cut off plaintext body if necessary to allow
  longer formatted messages.
* Updated dependencies to fix Python 3.13 compatibility.

[@domrim]: https://github.com/domrim
[@jkhsjdhjs]: https://github.com/jkhsjdhjs
[#253]: https://github.com/maubot/maubot/pull/253
[#240]: https://github.com/maubot/maubot/pull/240

# v0.5.0 (2024-08-24)

* Dropped Python 3.9 support.
* Updated Docker image to Alpine 3.20.
* Updated mautrix-python to 0.20.6 to support authenticated media.
* Removed hard dependency on SQLAlchemy.
* Fixed `main_class` to default to being loaded from the last module instead of
  the first if a module name is not explicitly specified.
  * This was already the [documented behavior](https://docs.mau.fi/maubot/dev/reference/plugin-metadata.html),
    and loading from the first module doesn't make sense due to import order.
* Added simple scheduler utility for running background tasks periodically or
  after a certain delay.
* Added testing framework for plugins (thanks to [@abompard] in [#225]).
* Changed `mbc build` to ignore directories declared in `modules` that are
  missing an `__init__.py` file.
  * Importing the modules at runtime would fail and break the plugin.
    To include non-code resources outside modules in the mbp archive,
    use `extra_files` instead.

[#225]: https://github.com/maubot/maubot/issues/225
[@abompard]: https://github.com/abompard

# v0.4.2 (2023-09-20)

* Updated Pillow to 10.0.1.
* Updated Docker image to Alpine 3.18.
* Added logging for errors for /whoami errors when adding new bot accounts.
* Added support for using appservice tokens (including appservice encryption)
  in standalone mode.

# v0.4.1 (2023-03-15)

* Added `in_thread` parameter to `evt.reply()` and `evt.respond()`.
  * By default, responses will go to the thread if the command is in a thread.
  * By setting the flag to `True` or `False`, the plugin can force the response
    to either be or not be in a thread.
* Fixed static files like the frontend app manifest not being served correctly.
* Fixed `self.loader.meta` not being available to plugins in standalone mode.
* Updated to mautrix-python v0.19.6.

# v0.4.0 (2023-01-29)

* Dropped support for using a custom maubot API base path.
  * The public URL can still have a path prefix, e.g. when using a reverse
    proxy. Both the web interface and `mbc` CLI tool should work fine with
    custom prefixes.
* Added `evt.redact()` as a shortcut for `self.client.redact(evt.room_id, evt.event_id)`.
* Fixed `mbc logs` command not working on Python 3.8+.
* Fixed saving plugin configs (broke in v0.3.0).
* Fixed SSO login using the wrong API path (probably broke in v0.3.0).
* Stopped using `cd` in the docker image's `mbc` wrapper to enable using
  path-dependent commands like `mbc build` by mounting a directory.
* Updated Docker image to Alpine 3.17.

# v0.3.1 (2022-03-29)

* Added encryption dependencies to standalone dockerfile.
* Fixed running without encryption dependencies installed.
* Removed unnecessary imports that broke on SQLAlchemy 1.4+.
* Removed unused alembic dependency.

# v0.3.0 (2022-03-28)

* Dropped Python 3.7 support.
* Switched main maubot database to asyncpg/aiosqlite.
  * Using the same SQLite database for crypto is now safe again.
* Added support for asyncpg/aiosqlite for plugin databases.
  * There are some [basic docs](https://docs.mau.fi/maubot/dev/database/index.html)
    and [a simple example](./examples/database) for the new system.
  * The old SQLAlchemy system is now deprecated, but will be preserved for
    backwards-compatibility until most plugins have updated.
* Started enforcing minimum maubot version in plugins.
  * Trying to upload a plugin where the specified version is higher than the
    running maubot version will fail.
* Fixed bug where uploading a plugin twice, deleting it and trying to upload
  again would fail.
* Updated Docker image to Alpine 3.15.
* Formatted all code using [black](https://github.com/psf/black)
  and [isort](https://github.com/PyCQA/isort).

# v0.2.1 (2021-11-22)

Docker-only release: added automatic moving of plugin databases from
`/data/plugins/*.db` to `/data/dbs`

# v0.2.0 (2021-11-20)

* Moved plugin databases from `/data/plugins` to `/data/dbs` in the docker image.
  * v0.2.0 was missing the automatic migration of databases, it was added in v0.2.1.
  * If you were using a custom path, you'll have to mount it at `/data/dbs` or
    move the databases yourself.
* Removed support for pickle crypto store and added support for SQLite crypto store.
  * **If you were previously using the dangerous pickle store for e2ee, you'll
    have to re-login with the bots (which can now be done conveniently with
    `mbc auth --update-client`).**
* Added SSO support to `mbc auth`.
* Added support for setting device ID for e2ee using the web interface.
* Added e2ee fingerprint field to the web interface.
* Added `--update-client` flag to store access token inside maubot instead of
  returning it in `mbc auth`.
  * This will also automatically store the device ID now.
* Updated standalone mode.
  * Added e2ee and web server support.
  * It's now officially supported and [somewhat documented](https://docs.mau.fi/maubot/usage/standalone.html).
* Replaced `_` with `-` when generating command name from function name.
* Replaced unmaintained PyInquirer dependency with questionary
  (thanks to [@TinfoilSubmarine] in [#139]).
* Updated Docker image to Alpine 3.14.
* Fixed avatar URLs without the `mxc://` prefix appearing like they work in the
  frontend, but not actually working when saved.

[@TinfoilSubmarine]: https://github.com/TinfoilSubmarine
[#139]: https://github.com/maubot/maubot/pull/139

# v0.1.2 (2021-06-12)

* Added `loader` instance property for plugins to allow reading files within
  the plugin archive.
* Added support for reloading `webapp` and `database` meta flags in plugins.
  Previously you had to restart maubot instead of just reloading the plugin
  when enabling the webapp or database for the first time.
* Added warning log if a plugin uses `@web` decorators without enabling the
  `webapp` meta flag.
* Updated frontend to latest React and dependency versions.
* Updated Docker image to Alpine 3.13.
* Fixed registering accounts with Synapse shared secret registration.
* Fixed plugins using `get_event` in encrypted rooms.
* Fixed using the `@command.new` decorator without specifying a name
  (i.e. falling back to the function name).

# v0.1.1 (2021-05-02)

No changelog.

# v0.1.0 (2020-10-04)

Initial tagged release.

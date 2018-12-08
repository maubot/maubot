# Maubot Management API
Most of the API is simple HTTP+JSON and has OpenAPI documentation (see
[spec.yaml](spec.yaml), [rendered](https://maubot.xyz/spec/)). However,
some parts of the API aren't documented in the OpenAPI document.

## Matrix API proxy
The full Matrix API can be accessed for each client with a request to
`/_matrix/maubot/v1/proxy/<user>/<path>`. `<user>` is the Matrix user
ID of the user to access the API as and `<path>` is the whole API
path to access (e.g. `/_matrix/client/r0/whoami`).

The body, headers, query parameters, etc are sent to the Matrix server
as-is, with a few exceptions:
* The `Authorization` header will be replaced with the access token
  for the Matrix user from the maubot database.
* The `access_token` query parameter will be removed.

## Log viewing
1. Open websocket to `/_matrix/maubot/v1/logs`.
2. Send authentication token as a plain string.
3. Server will respond with `{"auth_success": true}` and then with
   `{"history": ...}` where `...` is a list of log entries.
4. Server will send new log entries as JSON.

### Log entry object format
Log entries are a JSON-serialized form of Python log records.

Log entries will always have:
* `id` - A string that should uniquely identify the row. Currently
         uses the `relativeCreated` field of Python logging records.
* `msg` - The text in the entry.
* `time` - The ISO date when the log entry was created.

Log entries should also always have:
* `levelname` - The log level (e.g. `DEBUG` or `ERROR`).
* `levelno`   - The integer log level.
* `name`      - The name of the logger. Common values:
  * `maubot.client.<mxid>` - Client loggers (Matrix HTTP requests)
  * `maubot.instance.<id>` - Plugin instance loggers
  * `maubot.loader.zip`    - The zip plugin loader (plugins don't
                             have their own logs)
* `module`   - The Python module name where the log call happened.
* `pathname` - The full path of the file where the log call happened.
* `filename` - The file name portion of `pathname`
* `lineno`   - The line in code where the log call happened.
* `funcName` - The name of the function where the log call happened.

Log entries might have:
* `exc_info` - The formatted exception info if an exception was logged.
* `matrix_http_request` - The info about a Matrix HTTP request. Subfields:
  * `method`  - The HTTP method used.
  * `path`    - The API path used.
  * `content` - The content sent.
  * `user`    - The appservice user who the request was ran as.

## Debug file open
For debug and development purposes, the API and frontend support
clicking on lines in stack traces to open that line in the selected
editor.

### Configuration
First, the directory where maubot is run from must have a
`.dev-open-cfg.yaml` file. The file should contain the following
fields:
* `editor` - The command to run to open a file.
  * `$path` is replaced with the full file path.
  * `$line` is replaced with the line number.
* `pathmap` - A list of find-and-replaces to execute on paths.
  These are needed to map things like `.mbp` files to the extracted
  sources on disk. Each pathmap entry should have:
  * `find`    - The regex to match.
  * `replace` - The replacement. May insert capture groups with Python
                syntax (e.g. `\1`)

Example file:
```yaml
editor: pycharm --line $line $path
pathmap:
- find: "maubot/plugins/xyz\\.maubot\\.(.+)-v.+(?:-ts[0-9]+)?.mbp"
  replace: "mbplugins/\\1"
- find: "maubot/.venv/lib/python3.6/site-packages/mautrix"
  replace: "mautrix-python/mautrix"
```

### API
Clients can `GET /_matrix/maubot/v1/debug/open` to check if the file
open endpoint has been set up. The response is a JSON object with a
single field `enabled`. If the value is true, the endpoint can be used.

To open files, clients can `POST /_matrix/maubot/v1/debug/open` with
a JSON body containing
* `path` - The full file path to open
* `line` - The line number to open

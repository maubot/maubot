const proxy = require("http-proxy-middleware")

module.exports = function(app) {
    app.use(proxy("/_matrix/maubot/v1", { target: "http://localhost:29316" }))
    app.use(proxy("/_matrix/maubot/v1/logs", { target: "http://localhost:29316", ws: true }))
}

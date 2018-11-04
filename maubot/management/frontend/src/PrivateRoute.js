import React, { Component } from "react"
import { Route, Redirect } from "react-router-dom"

const PrivateRoute = ({ component, authed, ...rest }) => (
    <Route
        {...rest}
        render={(props) => authed === true
            ? <Component {...props} />
            : <Redirect to={{
                pathname: "/login",
                state: { from: props.location },
            }}/>}
    />
)

export default PrivateRoute

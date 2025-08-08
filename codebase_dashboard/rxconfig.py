"""Reflex configuration for the Codebase Dashboard."""

import reflex as rx

config = rx.Config(
    app_name="codebase_dashboard",
    frontend_port=3000,
    backend_port=3001,
    api_url="http://localhost:3001",
    deploy_url="http://localhost:3000",
    env=rx.Env.DEV,
)

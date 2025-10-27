#!/bin/bash
# Start browser-use MCP server with fixed config loading

cd "$(dirname "$0")"
exec .venv/bin/python3 -m browser_use.cli --mcp "$@"

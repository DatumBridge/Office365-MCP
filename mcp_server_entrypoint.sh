#!/bin/bash
cd "$(dirname "$0")"
uvicorn app.mcp_server:http_app --host 0.0.0.0 --port 8000

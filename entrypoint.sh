#!/bin/sh
set -e
uvicorn robust_fastapi_api.app:app --host 0.0.0.0 --port 8080

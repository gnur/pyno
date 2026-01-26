#!/usr/bin/env -S uv run --script
# 
# /// script
# requires-python = ">=3.13"
# dependencies = ["fastapi", "uvicorn[standard]"]
# ///

import os
import re
import argparse
import time
import threading
from datetime import date
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request

# The base directory for notes. Can be set with the PYNO_DIR environment variable.
BASE_DIR = Path("/home/erwin/obsidian/0 - drafts")


app = FastAPI()


@app.post("/note")
async def add_note(request: Request):
    """Adds the request body to the daily note, avoiding duplicates."""
    body = await request.body()
    content_to_add = body.decode("utf-8")

    today_filepath = BASE_DIR / "iphone-todos.md"

    with today_filepath.open("a") as f:
        f.write("\n - [ ] " + content_to_add)

    print(f"Content added to iphone-todos.md: {today_filepath}")
    return {"status": "success", "message": f"Content added to {today_filepath}"}


def start_api_server() -> None:
    """Starts the FastAPI server."""
    port = int(os.environ.get("PYNO_PORT", 8293))
    print(f"Starting API server on http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

def main() -> None:
    start_api_server()


if __name__ == "__main__":
    main()

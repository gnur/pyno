#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.13"
# dependencies = ["fastapi", "uvicorn[standard]", "pyyaml"]
# ///

import os
from datetime import datetime
from pathlib import Path

import json
import uvicorn
import yaml
from fastapi import FastAPI, Query, Request
from pydantic import BaseModel

# The base directory for notes. Can be set with the PYNO_DIR environment variable.
BASE_DIR = Path("/home/erwin/obsidian/")
DRAFTS_DIR = BASE_DIR / "0 - drafts"
POOPS_DIR = BASE_DIR / "2 - prive" / "poops"
WEBHOOK_DIR = BASE_DIR / "4 - webhook"


app = FastAPI()


class PoopEntry(BaseModel):
    loc: str
    wipes: str
    size: str
    bristol: str


@app.post("/webhook/{source}")
async def log_webhook(
    source: str, request: Request, typ: str = Query(default="webhook")
):
    """Records a webhook payload to an Obsidian markdown file with YAML frontmatter."""
    now = datetime.now()
    timestamp = now.isoformat(timespec="seconds")

    body_text = "<empty>"
    body_lang = ""

    try:
        body = await request.json()
        body_text = json.dumps(body, indent=2)
        body_lang = "json"
    except Exception:
        body_bytes = await request.body()
        body_text = body_bytes.decode("utf-8")

    data = {
        "timestamp": f"{timestamp}Z",
        "source": source,
        "type": typ,
    }

    subdir = WEBHOOK_DIR / str(now.year) / f"{now.month:02d}" / f"{now.day:02d}"
    subdir.mkdir(parents=True, exist_ok=True)

    filename = f"{source}-{now.hour:02d}:{now.minute:02d}:{now.second:02d}.md"
    filepath = subdir / filename

    with filepath.open("w") as f:
        f.write("---\n")
        yaml.dump(data, f, default_flow_style=False)
        f.write("---\n\n")
        f.write(f"```{body_lang}\n")
        f.write(body_text)
        f.write("\n```\n\n")
        f.write("```yaml\n")
        f.write(yaml.dump(dict(request.headers), default_flow_style=False))
        f.write("```\n")

    print(f"Webhook entry saved to: {filepath}")
    return {"status": "success", "message": f"Webhook entry saved to {filename}"}


@app.post("/poop")
async def add_poop(entry: PoopEntry):
    """Records a poop entry to an Obsidian markdown file with YAML frontmatter."""
    now = datetime.now()
    timestamp = now.isoformat(timespec="seconds")

    # Remove newlines from location
    loc = entry.loc.replace("\n", " ").replace("\r", " ")

    data = {
        "timestamp": f"{timestamp}Z",
        "location": loc,
        "wipes": entry.wipes,
        "size": entry.size,
        "bristol": entry.bristol,
        "location_name": "",
    }

    # Store in <year>/<month>/ subdirectory with filename <yyyy-mm-dd>.md
    # If file exists, add incrementing number suffix
    subdir = POOPS_DIR / str(now.year) / f"{now.month:02d}"
    subdir.mkdir(parents=True, exist_ok=True)

    base_filename = f"{now.year}-{now.month:02d}-{now.day:02d}"
    filepath = subdir / f"{base_filename}.md"

    counter = 1
    while filepath.exists():
        filepath = subdir / f"{base_filename}-{counter}.md"
        counter += 1

    with filepath.open("w") as f:
        f.write("---\n")
        yaml.dump(data, f, default_flow_style=False)
        f.write("---\n")

    print(f"Poop entry saved to: {filepath}")
    return {"status": "success", "message": f"Poop entry saved to {filepath}"}


@app.post("/note")
async def add_note(request: Request):
    """Adds the request body to the daily note, avoiding duplicates."""
    body = await request.body()
    content_to_add = body.decode("utf-8")

    today_filepath = DRAFTS_DIR / "iphone-todos.md"

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

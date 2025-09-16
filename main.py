#!/usr/bin/env -S uv run --script
# 
# /// script
# requires-python = ">=3.13"
# dependencies = ["schedule", "fastapi", "uvicorn[standard]"]
# ///

import os
import re
import argparse
import time
import threading
from datetime import date
from pathlib import Path

import schedule
import uvicorn
from fastapi import FastAPI, Request

# The base directory for notes. Can be set with the PYNO_DIR environment variable.
BASE_DIR = Path(os.path.expanduser(os.environ.get("PYNO_DIR", "~/ll")))


def get_today_note_path() -> Path:
    """Returns the path to today's daily note."""
    today = date.today()
    year = today.strftime("%Y")
    month = today.strftime("%m")
    today_str = today.strftime("%Y-%m-%d")
    note_dir = BASE_DIR / year / month
    return note_dir / f"{today_str}.md"


app = FastAPI()


@app.post("/note")
async def add_note(request: Request):
    """Adds the request body to the daily note, avoiding duplicates."""
    body = await request.body()
    content_to_add = body.decode("utf-8")

    today_filepath = get_today_note_path()

    if not today_filepath.exists():
        print("Daily note does not exist, creating it.")
        create_daily_note()

    with today_filepath.open("r") as f:
        if content_to_add in f.read():
            message = "Content already present in daily note."
            print(message)
            return {"status": "skipped", "message": message}

    with today_filepath.open("a") as f:
        f.write("\n\n---\n\n" + content_to_add)

    print(f"Content added to daily note: {today_filepath}")
    return {"status": "success", "message": f"Content added to {today_filepath}"}


def create_daily_note() -> None:
    """
    Creates a daily note.
    - Copies all unfinished todo items from the last previous note.
    - Adds the date of the last daily note to todo items without a date.
    """
    today_filepath = get_today_note_path()
    today_filepath.parent.mkdir(parents=True, exist_ok=True)

    if today_filepath.exists():
        print(f"Note for today already exists: {today_filepath}")
        return

    # Find the last daily note
    # The pattern should match yyyy-mm-dd.md in a yyyy/mm directory
    daily_notes = sorted(list(BASE_DIR.glob("????/??/????-??-??.md")))

    # Exclude today's note if it somehow got in the list (it shouldn't if we check for existence first)
    daily_notes = [p for p in daily_notes if p.name != today_filepath.name]

    last_note_path = daily_notes[-1] if daily_notes else None

    content = f"# {today_filepath.stem}\n\n## todo\n"

    todos = []
    if last_note_path:
        last_note_date_str = last_note_path.stem
        try:
            last_note_content = last_note_path.read_text()
        except Exception as e:
            print(f"Error reading last note {last_note_path}: {e}")
            last_note_content = ""

        # A single regex to find and parse todo items.
        # It captures the prefix, an optional date, and the task.
        todo_pattern = re.compile(r"^(\s*-\s*\[\s*\]\s*)((\d{4}-\d{2}-\d{2}:\s*)?)(.*)")

        for line in last_note_content.splitlines():
            match = todo_pattern.match(line)
            if match:
                prefix = match.group(1)
                date_part = match.group(2)
                task = match.group(4).strip()

                if date_part:
                    # Todo item already has a date, so we keep it as is.
                    todos.append(line)
                else:
                    # Todo item does not have a date, so we add it.
                    if task:
                        new_line = f"{prefix.rstrip()} {last_note_date_str}: {task}"
                    else:  # handle empty todo
                        new_line = f"{prefix.rstrip()} {last_note_date_str}:"
                    todos.append(new_line)

    # Sort todos in reverse order, as in the bash script
    todos.sort(reverse=True)

    if todos:
        content += "\n".join(todos)

    today_filepath.write_text(content)
    print(f"Created daily note: {today_filepath}")


def cleanup_last_note() -> None:
    """
    Deletes the last daily note if it contains no unique information.

    Unique information is any content other than:
    - The note's date heading.
    - The '## todo' heading.
    - Completed todo items ('- [x] ...').
    - Unfinished todo items ('- [ ] ...').
    - Empty lines.
    """
    today_note_path = get_today_note_path()
    if not today_note_path.exists():
        # This can happen if the script is run with other arguments in the future.
        print("Today's note does not exist, skipping cleanup.")
        return

    # Find all daily notes
    daily_notes = sorted(list(BASE_DIR.glob("????/??/????-??-??.md")))

    # Get the last note before today
    daily_notes_before_today = [p for p in daily_notes if p.name < today_note_path.name]

    if not daily_notes_before_today:
        print("No previous daily note to clean up.")
        return

    last_note_path = daily_notes_before_today[-1]

    try:
        last_note_content = last_note_path.read_text()
    except Exception as e:
        print(f"Error reading last note {last_note_path}: {e}")
        return

    unique_content = []
    for line in last_note_content.splitlines():
        stripped_line = line.strip()
        if not stripped_line:
            continue  # Ignore empty lines
        if stripped_line.startswith(f"# {last_note_path.stem}"):
            continue  # Ignore date heading
        if stripped_line == "## todo":
            continue  # Ignore todo heading
        if stripped_line.startswith("- [x]"):
            continue  # Ignore completed todos
        if re.match(r"^\s*-\s*\[\s*\]", stripped_line):
            continue  # Ignore unfinished todos

        unique_content.append(line)

    if not unique_content:
        print(f"No unique information found in {last_note_path}. Deleting note.")
        last_note_path.unlink()
    else:
        print(f"Found unique information in {last_note_path}. Keeping note.")


def run_once() -> None:
    """Creates the daily note and cleans up the previous one."""
    print("Running daily job: creating note and cleaning up...")
    create_daily_note()
    cleanup_last_note()


def start_watcher() -> None:
    """Runs the daily note creation automatically after midnight."""
    print("Starting watcher...")
    schedule.every().day.at("00:10").do(run_once)
    while True:
        schedule.run_pending()
        time.sleep(60)


def start_api_server() -> None:
    """Starts the FastAPI server."""
    port = int(os.environ.get("PYNO_PORT", 8293))
    print(f"Starting API server on http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

def serve() -> None:
    """Runs the watcher in the background and starts the API server."""
    run_once()
    watcher_thread = threading.Thread(target=start_watcher, daemon=True)
    watcher_thread.start()
    start_api_server()

def main() -> None:
    """
    Main entry point for the script.

    Run without arguments to show help.
    Run with 'watch' to start the scheduler.
    Run with 'api' to start the API server.
    Run with 'serve' to run both the watcher and API server.
    """
    parser = argparse.ArgumentParser(
        description="A script to manage daily notes.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=["once", "watch", "api", "serve"],
        help=(
            "The command to run. "
            "'once': Create today's note and cleanup previous. "
            "'watch': Run once and start the scheduler. "
            "'api': Start the API server. "
            "'serve': Run once and start both watcher and API server."
        ),
    )
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    match args.command:
        case "once":
            run_once()
        case "watch":
            run_once()
            start_watcher()
        case "api":
            start_api_server()
        case "serve":
            serve()


if __name__ == "__main__":
    main()

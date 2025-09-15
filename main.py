# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///

import os
import re
from datetime import date
from pathlib import Path

# The base directory for notes.
BASE_DIR = Path(os.path.expanduser("~/ll"))

def create_daily_note() -> None:
    """
    Creates a daily note.
    - Copies all unfinished todo items from the last previous note.
    - Adds the date of the last daily note to todo items without a date.
    """
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    year = today.strftime("%Y")
    month = today.strftime("%m")

    note_dir = BASE_DIR / year / month
    note_dir.mkdir(parents=True, exist_ok=True)

    today_filepath = note_dir / f"{today_str}.md"

    if today_filepath.exists():
        print(f"Note for today already exists: {today_filepath}")
        return

    # Find the last daily note
    # The pattern should match yyyy-mm-dd.md in a yyyy/mm directory
    daily_notes = sorted(list(BASE_DIR.glob("????/??/????-??-??.md")))
    
    # Exclude today's note if it somehow got in the list (it shouldn't if we check for existence first)
    daily_notes = [p for p in daily_notes if p.name != f"{today_str}.md"]

    last_note_path = daily_notes[-1] if daily_notes else None

    content = f"# {today_str}\n\n## todo\n"
    
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


def main() -> None:
    # For now, the main function will just call create_daily_note()
    create_daily_note()


if __name__ == "__main__":
    main()
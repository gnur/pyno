#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.13"
# dependencies = ["fastapi", "uvicorn[standard]", "pyyaml"]
# ///

import csv
import os
import re
import argparse
import time
import threading
from datetime import date, datetime
from pathlib import Path

import yaml
from pydantic import BaseModel

# The base directory for notes. Can be set with the PYNO_DIR environment variable.
BASE_DIR = Path("./poops")
DRAFTS_DIR = BASE_DIR / "0 - drafts"
POOPS_DIR = BASE_DIR / "2 - prive" / "poops"


class PoopEntry(BaseModel):
    loc: str
    wipes: str
    size: str
    bristol: str


async def add_poop(entry: PoopEntry):
    """Records a poop entry to an Obsidian markdown file with YAML frontmatter."""
    now = datetime.now()
    timestamp = now.isoformat()

    # Remove newlines from location
    loc = entry.loc.replace("\n", " ").replace("\r", " ")

    data = {
        "timestamp": timestamp,
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



def amount_to_size(amount: int) -> str:
    """Convert amount (1-10) to size (xs, s, m, l, xl)."""
    if amount <= 1:
        return "xs"
    elif amount <= 3:
        return "s"
    elif amount <= 5:
        return "m"
    elif amount <= 7:
        return "l"
    else:
        return "xl"


def stickiness_to_wipes(stickiness: int) -> str:
    """Convert stickiness (0-10+) to wipes category."""
    if stickiness == 0:
        return "golden drop"
    elif stickiness <= 3:
        return "okay"
    else:
        return "marker"


def bristol_to_category(bristol: int) -> str:
    """Convert bristol scale (1-7) to category."""
    if bristol == 1:
        return "rabbit"
    elif bristol <= 3:
        return "clumpy"
    elif bristol <= 5:
        return "regular"
    elif bristol == 6:
        return "slurry"
    else:
        return "water"


def load_locations(csv_path: str = "locations.csv") -> list[dict]:
    """Load locations from CSV file."""
    locations = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            locations.append({
                "name": row["name"].strip(),
                "lat": float(row["latitude"]),
                "lon": float(row["longitude"]),
            })
    return locations


def find_closest_location(lat: float, lon: float, locations: list[dict]) -> str:
    """Find the closest location name based on lat/lon using Euclidean distance."""
    if not locations:
        return ""

    closest = min(
        locations,
        key=lambda loc: (loc["lat"] - lat) ** 2 + (loc["lon"] - lon) ** 2
    )
    return closest["name"]


def import_poops_csv(csv_path: str = "poops.csv", locations_path: str = "locations.csv") -> None:
    """Import poop entries from CSV file."""
    locations = load_locations(locations_path)

    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)

        for row in reader:
            timestamp = row["time"]
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

            amount = int(row["amount"])
            bristol = int(row["bristol"])
            stickiness = int(row["stickiness"])
            latitude = float(row["latitude"])
            longitude = float(row["longitude"])

            size = amount_to_size(amount)
            wipes = stickiness_to_wipes(stickiness)
            bristol_cat = bristol_to_category(bristol)
            location_name = find_closest_location(latitude, longitude, locations)

            data = {
                "timestamp": timestamp,
                "location": f"{latitude},{longitude}",
                "wipes": wipes,
                "size": size,
                "bristol": bristol_cat,
                "location_name": location_name,
            }

            # Store in <year>/<month>/ subdirectory with filename <yyyy-mm-dd>.md
            subdir = POOPS_DIR / str(dt.year) / f"{dt.month:02d}"
            subdir.mkdir(parents=True, exist_ok=True)

            base_filename = f"{dt.year}-{dt.month:02d}-{dt.day:02d}"
            filepath = subdir / f"{base_filename}.md"

            counter = 1
            while filepath.exists():
                filepath = subdir / f"{base_filename}-{counter}.md"
                counter += 1

            with filepath.open("w") as out:
                out.write("---\n")
                yaml.dump(data, out, default_flow_style=False)
                out.write("---\n")

            print(f"Imported: {filepath}")


def main() -> None:
    import_poops_csv()


if __name__ == "__main__":
    main()

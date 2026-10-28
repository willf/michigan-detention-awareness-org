#!/usr/bin/env python3
"""Rebuild the memorial's browser data from the Detention Mortality CSV."""

import argparse
import csv
from datetime import date
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.error import URLError
from urllib.request import Request, urlopen


SOURCE_URL = "https://detentionmortality.com/detainee_deaths_data.csv"
DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent / "memorial" / "data.js"
CUTOFF = "2024-01-01"  # Initial display only; keep all historical records.
FIELDS = {
    "name": "Name",
    "nationality": "Nationality",
    "age": "Age",
    "dateOfDeath": "Date of Death",
    "lastDetentionFacility": "Last Detention Facility",
    "deathLocationCity": "Actual Death Location City",
    "deathLocationState": "Actual Death Location State",
}
ABBREVIATIONS = set(
    "AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO "
    "MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI "
    "WY DC PR MP GU VI AS ICE ERO".split()
)


def facility_name(value):
    """Match the memorial's existing title casing, retaining state codes/ICE/ERO."""
    if value is None:
        return None
    return re.sub(
        r"\b\w+\b",
        lambda match: match[0].upper() if match[0].upper() in ABBREVIATIONS else match[0],
        value.title(),
    )


def build_data(csv_text):
    reader = csv.DictReader(io.StringIO(csv_text.lstrip("\ufeff")), strict=True)
    missing = set(FIELDS.values()) - set(reader.fieldnames or [])
    if missing:
        raise ValueError("Missing CSV columns: " + ", ".join(sorted(missing)))
    records = []
    ids = set()
    for row in reader:
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f"CSV row ending at line {reader.line_num} has the wrong number of fields")
        record = {key: row[column].strip() or None for key, column in FIELDS.items()}
        if not record["name"]:
            raise ValueError(f"Missing name at CSV line {reader.line_num}")
        death_date = record["dateOfDeath"]
        if not death_date or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", death_date):
            raise ValueError(f"Invalid date for {record['name']}: {death_date!r}")
        date.fromisoformat(death_date)  # Reject impossible calendar dates too.
        age = record["age"]
        if age is not None:
            if not re.fullmatch(r"[0-9]+", age) or not 0 <= int(age) <= 120:
                raise ValueError(f"Invalid age for {record['name']}: {age!r}")
            record["age"] = int(age)
        record_id = re.sub(r"[^a-z0-9]+", "-", record["name"].lower()).strip("-")
        if not record_id or record_id in ids:
            raise ValueError(f"Empty or duplicate ID for {record['name']}; review the source before updating")
        ids.add(record_id)
        record["lastDetentionFacility"] = facility_name(record["lastDetentionFacility"])
        records.append({"id": record_id, **record})
    if not records:
        raise ValueError("CSV contains no records; refusing to replace memorial data")
    records.sort(key=lambda record: record["name"].casefold())
    records.sort(key=lambda record: record["dateOfDeath"], reverse=True)
    data = {"cutoff": CUTOFF, "source": SOURCE_URL, "records": records}
    return "window.MEMORIAL_DATA = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Read a local CSV instead of downloading")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output JS path")
    parser.add_argument("--check", action="store_true", help="Do not write; exit 1 if output differs")
    args = parser.parse_args()
    try:
        if args.input:
            csv_text = args.input.read_text(encoding="utf-8-sig")
        else:
            request = Request(SOURCE_URL, headers={"User-Agent": "MichiganDetentionAwareness-MemorialUpdater/1.0"})
            with urlopen(request, timeout=60) as response:
                csv_text = response.read().decode("utf-8-sig")
        generated = build_data(csv_text)
        if args.output.exists() and args.output.read_bytes() == generated.encode("utf-8"):
            print(f"Already up to date: {args.output}")
            return 0
        if args.check:
            print(f"Update available: {args.output}")
            return 1
        # Validate everything first, then atomically replace the file on the same filesystem.
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(dir=args.output.parent, delete=False) as temporary:
                temporary_path = Path(temporary.name)
                temporary.write(generated.encode("utf-8"))
            temporary_path.chmod(0o644)
            os.replace(temporary_path, args.output)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
        print(f"Updated: {args.output}")
        return 0
    except (OSError, URLError, ValueError, csv.Error) as error:
        print(f"Memorial update failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

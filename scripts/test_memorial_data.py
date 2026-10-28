"""Offline regression tests for source conversion and safe updates."""

import csv
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("build-memorial-data.py")
SPEC = importlib.util.spec_from_file_location("memorial_data", SCRIPT)
updater = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(updater)


def source_csv(*overrides):
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=list(updater.FIELDS.values()))
    writer.writeheader()
    for override in overrides:
        row = dict(zip(updater.FIELDS.values(), [
            "María Example", "Peru", "47", "2026-09-29",
            "RICHWOOD ICE CENTER LA", "Monroe", "LA",
        ]))
        row.update(override)
        writer.writerow(row)
    return stream.getvalue()


def records(csv_text):
    generated = updater.build_data(csv_text)
    return json.loads(generated[len("window.MEMORIAL_DATA = "):-2])["records"]


class MemorialDataTests(unittest.TestCase):
    def test_conversion_handles_bom_quoted_fields_unicode_and_missing_details(self):
        record = records("\ufeff" + source_csv({
            "Actual Death Location City": "City, with comma\nand newline",
            "Nationality": "", "Age": "", "Actual Death Location State": "",
        }))[0]
        self.assertEqual(record["id"], "mar-a-example")
        self.assertEqual(record["name"], "María Example")
        self.assertIsNone(record["age"])
        self.assertIsNone(record["nationality"])
        self.assertIsNone(record["deathLocationState"])
        self.assertEqual(record["lastDetentionFacility"], "Richwood ICE Center LA")
        self.assertEqual(record["deathLocationCity"], "City, with comma\nand newline")

    def test_keeps_history_and_sorts_independently_of_source_order(self):
        rows = [
            {"Name": "Z Example", "Date of Death": "2026-01-01"},
            {"Name": "Old Example", "Date of Death": "2003-10-07"},
            {"Name": "A Example", "Date of Death": "2026-01-01"},
        ]
        self.assertEqual(updater.build_data(source_csv(*rows)),
                         updater.build_data(source_csv(*reversed(rows))))
        self.assertEqual([r["name"] for r in records(source_csv(*rows))],
                         ["A Example", "Z Example", "Old Example"])

    def test_rejects_missing_columns_empty_or_malformed_csv(self):
        for source in ["<html>Unavailable</html>", source_csv(),
                       source_csv({}) + "too,few,columns\n",
                       source_csv({}) + '"unclosed quote']:
            with self.subTest(source=source), self.assertRaises((ValueError, csv.Error)):
                updater.build_data(source)

    def test_rejects_invalid_required_values(self):
        for override in [
            {"Name": ""}, {"Date of Death": ""}, {"Date of Death": "2026-02-30"},
            {"Date of Death": "09/29/2026"}, {"Age": "unknown"}, {"Age": "-1"},
        ]:
            with self.subTest(override=override), self.assertRaises(ValueError):
                updater.build_data(source_csv(override))

    def test_rejects_colliding_ids(self):
        with self.assertRaisesRegex(ValueError, "duplicate ID"):
            updater.build_data(source_csv({"Name": "A-B"}, {"Name": "A B"}))

    def test_cli_check_noop_and_failed_update_preserve_output(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.csv"
            output = Path(directory) / "data.js"
            source.write_text(source_csv({}), encoding="utf-8")
            output.write_text("previous data", encoding="utf-8")

            def run(*args):
                return subprocess.run([
                    sys.executable, str(SCRIPT), "--input", str(source),
                    "--output", str(output), *args,
                ], capture_output=True, text=True)

            self.assertEqual(run("--check").returncode, 1)
            self.assertEqual(output.read_text(), "previous data")
            self.assertEqual(run().returncode, 0)
            modified = output.stat().st_mtime_ns
            self.assertEqual(run("--check").returncode, 0)
            self.assertEqual(run().returncode, 0)
            self.assertEqual(output.stat().st_mtime_ns, modified)
            generated = output.read_bytes()
            source.write_text("invalid source", encoding="utf-8")
            self.assertEqual(run().returncode, 2)
            self.assertEqual(output.read_bytes(), generated)


if __name__ == "__main__":
    unittest.main()

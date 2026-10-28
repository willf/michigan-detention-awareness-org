# michigan-detention-awareness-org

Website for [https://michigan-detention-awareness.org](https://michigan-detention-awareness.org).

Weekly census numbers for Michigan ICE detention facilities. The homepage lets
visitors select a facility and review its historical weekly census.

## Updating the facility data

The website reads its facility history from
`assets/facility-weekly-data.js`. This is a generated file; do not edit it by
hand. Its source is `assets/detention-stints_summary.parquet`.

The generator requires Bash and the DuckDB command-line interface. On macOS,
install DuckDB with Homebrew if needed:

```sh
brew install duckdb
```

Other installation options are available on the
[official DuckDB installation page](https://duckdb.org/install/). Confirm that
DuckDB is available before continuing:

```sh
duckdb --version
```

To update the website after receiving a new Parquet file:

1. Replace `assets/detention-stints_summary.parquet` with the new file.
2. From the project root, run:

   ```sh
   ./scripts/build-facility-weekly-data.sh
   ```

3. Review the generated changes and open the homepage locally to confirm the
   latest week, facility names, and census values.

The script includes each facility's latitude and longitude, rounds weekly
averages to whole people, orders observations chronologically, and keeps
Baldwin (`NRLKCMI`) as the default facility. It writes to a temporary location
first, so an error will not replace the last working JavaScript file.

### Alternate paths

The first optional argument is the input Parquet file and the second is the
output JavaScript file:

```sh
./scripts/build-facility-weekly-data.sh path/to/input.parquet path/to/output.js
```

## Adding supplemental resident counts

Edit `assets/facility-observations.json` to add dated counts from other sources.
Append a record for each new report, preserving previous observations:

```json
{
  "facilityCode": "NRLKCMI",
  "date": "2026-10-06",
  "count": 1342,
  "measurement": "snapshot",
  "source": "Site editor report",
  "sourceUrl": null
}
```

Use the facility code from `assets/facility-weekly-data.js`, an ISO date
(`YYYY-MM-DD`), a nonnegative integer count, and a source name. Replace
"Site editor report" with the publication or organization when available;
`sourceUrl` can be an HTTP/HTTPS link or `null`.

The headline and facility selector use each facility's most recent observation.
Supplemental observations take precedence on the same date and are labeled
"As of" with a source beneath the headline. Older reports do not replace newer
weekly data. The Census History table includes weekly averages and dated snapshots, with
measurement labels and snapshot sources. Changes compare consecutive reports regardless of source or measurement type. The trend
combines weekly averages and supplemental snapshots within 26 weeks of the latest
report, using actual dates for horizontal spacing. Outlined dots identify
snapshots; lines connect available reports without filling gaps.

No Parquet rebuild is needed for supplemental updates. Serve the site over HTTP
when previewing locally (for example, `python3 -m http.server`), since loading
the JSON file requires HTTP. If supplemental data cannot be loaded, the page
falls back to the generated weekly data.

## Updating the memorial data

`memorial/data.js` is generated from the
[ICE Detention Mortality Dashboard CSV](https://detentionmortality.com/detainee_deaths_data.csv).
Use Python 3.9 or newer; no additional packages are required:

```sh
python3 scripts/build-memorial-data.py
```

This downloads the CSV and recreates the fields used by `memorial/index.html`,
with records ordered newest first. It retains the full history and the initial
display cutoff of January 1, 2024. Names retain their source spelling; facility
names use the memorial's existing title casing with state codes, ICE, and ERO
capitalized. Blank optional fields become `null`.

The output is deterministic: unchanged memorial fields do not rewrite the file,
even if the CSV row order or unused columns change. Missing columns, invalid
dates or ages, missing names, duplicate IDs, malformed CSV, and empty datasets
fail before replacing the existing file. Valid source corrections and removals
are reflected in the output, so review the diff before deploying.

To check without writing, or rebuild from a downloaded CSV:

```sh
python3 scripts/build-memorial-data.py --check
python3 scripts/build-memorial-data.py --input path/to/detainee_deaths_data.csv
```

`--check` exits with status 0 when current, 1 when an update is available, and 2
on error. `--output path/to/data.js` lets you preview generated data separately.
The default output path is resolved relative to the script, so it also works
when run outside the project root. To run the offline conversion tests:

```sh
python3 -B -m unittest discover -s scripts -p 'test_memorial_data.py'
```

### Automatic checks

`.github/workflows/update-memorial-data.yml` checks daily at 13:23 UTC
(9:23 a.m. Detroit during daylight saving time, 8:23 a.m. during standard time).
It can also be run from **Actions → Update memorial data → Run workflow**.
The workflow tests the converter, rebuilds the file, and opens or updates a
single pull request on `automation/update-memorial-data` when there are changes.
Merge that PR to include the update in the site's normal deployment.

After committing and pushing the workflow to the default branch, enable
**Settings → Actions → General → Workflow permissions → Allow GitHub Actions
to create and approve pull requests** if it is not already enabled. The
workflow uses the built-in `GITHUB_TOKEN` with contents and pull-request write
permissions; no additional secret is required. See the
[create-pull-request action documentation](https://github.com/peter-evans/create-pull-request#workflow-permissions).

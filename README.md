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

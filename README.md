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

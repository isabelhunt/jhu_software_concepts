# Module 4: Grad Cafe Analytics

Isabel Hunt (`ihunt5`)

A Flask application for collecting graduate application results and displaying
analysis. Module 4 includes automated tests, coverage checks, Sphinx documentation,
and a GitHub Actions workflow.

To view the full documentation: 
https://jhu-software-concepts-hunt.readthedocs.io/en/latest/#

All commands below run from `module_4/` unless stated otherwise.

## Environment and dependencies

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows, activate with `venv\Scripts\activate` instead.

Install application, test, and documentation dependencies together:

```bash
python -m pip install -r requirements.txt
```

This shared file includes the LLM runtime, so CI and documentation builds also
install its dependencies.

The application uses Unix file locking through `fcntl`; run the Flask app and
tests on Linux, macOS, or WSL.

## Database configuration

For the live application, start PostgreSQL and create a database and login.
Copy the example configuration:

```bash
cp src/.env.example src/.env
```

Set all five variables in `src/.env`:

```dotenv
DB_NAME=your_database
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

`src/db_config.py` reads this file. Existing environment variables take precedence,
and `DB_PORT` must be an integer. Keep real credentials out of version control.
The analysis page requires an `applicants` table populated with applicant records.

## Run the Flask application

```bash
python -m src.run
```

Open <http://localhost:8080/>. The development server runs with debug mode enabled.

- **Pull Data** sends `POST /pull-data`. The route is intended to run the scraper,
  which calls the cleaner, then LLM enrichment and the database loader. Repeated
  URLs are skipped; records without URLs are deduplicated by their stored values.
- **Update Analysis** sends `GET /update-analysis` and recalculates the six
  displayed answers with the ORM queries. Decimal answers display two places.
- While a pull holds the lock, another pull or analysis update returns `409`.
  Failed pulls return `500`; unavailable database analysis returns `503`.

**Current script limitation:** the direct-execution blocks in `scrape.py`,
`load_data.py`, `query_data.py`, and `orm_queries.py` are commented out. The
Pull Data route launches scripts as subprocesses, so its live pipeline needs
those entry points enabled before it can perform the intended work. The loader
also uses a package-relative import, so direct execution must be reconciled with
module execution (`python -m src.load_data`). Tests replace the subprocess calls
and exercise the functions directly; passing tests do not establish that the
live subprocess entry points work.

After enabling their entry points, run SQL and ORM reports as modules:

```bash
python -m src.query_data
python -m src.orm_queries
```

## Tests and coverage

```bash
python -m pytest tests --strict-markers
```

`pytest.ini` measures coverage of `src` and requires **100% coverage**. Tests use
fake records, mocked external services, and in-memory SQLite databases; the local
suite does not require PostgreSQL, Chrome, or a running LLM service.

Select a category with `-m`:

| Marker | Coverage area |
| --- | --- |
| `web` | Flask app creation, routes, and page content |
| `buttons` | Pull Data, Update Analysis, busy responses, and failures |
| `analysis` | Answer labels, decimal formatting, and query output |
| `db` | Configuration, connections, loading, duplicates, and stored fields |
| `integration` | Pull and analysis flows using shared fake records |

A subset of tests may not satisfy the full-suite coverage threshold. For a focused
run without the configured coverage options:

```bash
python -m pytest tests/test_buttons.py -o addopts='' -q
```

The tests simulate browser requests with Flask's test client. They do not click
buttons in an actual browser. SQLite and mocks also do not validate all
PostgreSQL-specific behavior.

## Documentation
To view the full documentation: 
https://jhu-software-concepts-hunt.readthedocs.io/en/latest/#

Sphinx configuration and documentation sources live in `docs/`. Autodoc imports
application modules from `src/` and renders their Sphinx-style docstrings.

Build HTML documentation and treat warnings as errors:

```bash
python -m sphinx -b html -W --keep-going docs _build/html
```

Open `_build/html/index.html` to view the result. Alternatively, use `make html`
or `make.bat html` with Sphinx installed in the active environment.

Read the Docs uses the repository-root `.readthedocs.yaml`, which points to
`module_4/docs/conf.py` and installs `module_4/requirements.txt`.

## Continuous integration

The repository-root `.github/workflows/ci.yml` runs on pushes, pull requests, and
manual dispatch. It starts PostgreSQL 16, waits for its health check, installs
the shared dependencies, verifies a real connection, creates the test tables, and runs
pytest with strict marker checking and the configured coverage threshold.

The workflow database uses disposable test credentials. The suite's mocked and
SQLite tests remain offline even though CI also checks PostgreSQL connectivity.

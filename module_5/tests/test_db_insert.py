import json
import sqlite3
import sys
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src import clean, db_config, models
from src import load_data as data_loader
from src.board import create_app, pages
from src.load_data import load_data


@pytest.mark.db
def test_load_data_skips_blank_json_lines(tmp_path, insertion_db):
    connection, cursor, rows = insertion_db
    source = tmp_path / "applicants.jsonl"
    records = [
        {"program": "Computer Science", "url": "https://example.com/1"},
        {"program": "Mathematics", "url": "https://example.com/2"},
    ]
    source.write_text(
        "\n \t\n" + json.dumps(records[0]) + "\n\n  \n" + json.dumps(records[1]) + "\n\n",
        encoding="utf-8",
    )

    assert load_data(connection, file_path=source) == 2
    assert [(row[0], row[3]) for row in rows] == [
        (record["program"], record["url"]) for record in records
    ]
    cursor.executemany.assert_called_once()


@pytest.mark.db
@pytest.mark.parametrize("invalid_line, cause", [
    ('{"GPA": "invalid"}', ValueError),
    ('{"GPA": []}', TypeError),
    ('null', AttributeError),
    ('{"date_added": "not-a-date"}', ValueError),
    ('{broken json}', ValueError),
], ids=["invalid-score", "wrong-score-type", "not-an-object", "invalid-date", "invalid-json"])
def test_load_data_reports_invalid_record(tmp_path, insertion_db, invalid_line, cause):
    connection, cursor, rows = insertion_db
    source = tmp_path / "applicants.jsonl"
    source.write_text(
        json.dumps({"program": "Computer Science"}) + "\n\n" + invalid_line + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=r"^Invalid record on line 3: ") as error:
        load_data(connection, file_path=source)

    assert isinstance(error.value.__cause__, cause)
    assert rows == []
    connection.transaction.assert_not_called()
    cursor.executemany.assert_not_called()


@pytest.mark.db
def test_connect_db_builds_url_and_returns_engine(mocker, capsys):
    settings = {
        "db_name": "test_applicants", "db_user": "test_user",
        "db_password": "fake:p@ss/word", "db_host": "localhost", "db_port": 5433,
    }
    get_settings = mocker.patch.object(models, "get_db_settings", return_value=settings)
    create_engine = mocker.patch.object(models, "create_engine")
    engine = create_engine.return_value

    result = models.Applicant.connect_db()

    get_settings.assert_called_once_with()
    create_engine.assert_called_once()
    url = create_engine.call_args.args[0]
    assert url.drivername == "postgresql+psycopg"
    assert url.username == settings["db_user"]
    assert url.password == settings["db_password"]
    assert url.host == settings["db_host"]
    assert url.port == settings["db_port"]
    assert url.database == settings["db_name"]
    engine.connect.assert_called_once_with()
    engine.connect.return_value.__enter__.assert_called_once_with()
    engine.connect.return_value.__exit__.assert_called_once_with(None, None, None)
    assert result is engine
    assert capsys.readouterr().out == "Connection was successful\n"

    connect = mocker.patch.object(data_loader.psycopg, "connect")
    result = data_loader.create_connection(**settings)
    connect.assert_called_once_with(
        dbname=settings["db_name"], user=settings["db_user"],
        password=settings["db_password"], host=settings["db_host"],
        port=settings["db_port"],
    )
    assert result is connect.return_value
    assert capsys.readouterr().out == "Connection to PostgreSQL DB successful\n"

    connect.side_effect = data_loader.OperationalError("Simulated connection failure")
    assert data_loader.create_connection(**settings) is None
    assert capsys.readouterr().out == "The error 'Simulated connection failure' occurred\n"


@pytest.mark.db
def test_scrape_timeout_saves_collected_entries(monkeypatch, mocker, tmp_path, capsys):
    monkeypatch.setitem(sys.modules, "clean", clean)
    from src import scrape

    monkeypatch.setattr(clean, "__file__", str(tmp_path / "clean.py"))
    first_driver = mocker.Mock()
    first_driver.page_source = """
        <table><tbody>
        <tr><td>Stanford University</td><td>Computer Science<br>PhD</td>
            <td>Sep 20, 2026</td><td>Accepted</td>
            <td><a href="/result/101">Details</a></td></tr>
        <tr><td colspan="5">Fall 2026 American GPA 3.75</td></tr>
        </tbody></table>
        <a href="/survey?cursor=next">Next</a>
    """
    timeout_driver = mocker.Mock()
    chrome = mocker.patch.object(
        scrape.webdriver, "Chrome", side_effect=[first_driver, timeout_driver]
    )
    wait = mocker.patch.object(scrape, "WebDriverWait")
    wait.return_value.until.side_effect = [True, scrape.TimeoutException("Simulated timeout")]
    save = mocker.spy(scrape, "save_data")
    cleaner = mocker.spy(scrape, "clean_data")

    scrape.main()

    stored = json.loads((tmp_path / "applicant_data.json").read_text())
    assert len(stored) == 1
    assert stored[0]["url"] == "https://www.thegradcafe.com/result/101"
    assert stored[0]["program"] == "Computer Science"
    assert stored[0]["GPA"] == "3.75"
    save.assert_called_once_with(stored)
    cleaner.assert_called_once()
    assert chrome.call_count == 2
    timeout_driver.get.assert_called_once_with("https://www.thegradcafe.com/survey?cursor=next")
    first_driver.quit.assert_called_once_with()
    timeout_driver.quit.assert_called_once_with()
    output = capsys.readouterr().out
    assert "Page load timed out. Saving collected entries." in output
    assert "You have reached" not in output


@pytest.mark.db
@pytest.mark.parametrize("timeout", [False, True], ids=["resume", "timeout"])
def test_scrape_resumes_existing_json(monkeypatch, mocker, tmp_path, capsys, timeout):
    monkeypatch.setitem(sys.modules, "clean", clean)
    from src import scrape

    monkeypatch.setattr(clean, "__file__", str(tmp_path / "clean.py"))
    saved_url = "https://www.thegradcafe.com/survey?cursor=old"
    next_url = "https://www.thegradcafe.com/survey?cursor=new"
    existing = [{"url": "https://www.thegradcafe.com/result/100",
                 "program": "Mathematics", "source_page_url": saved_url}]
    source = tmp_path / "applicant_data.json"
    source.write_text(json.dumps(existing), encoding="utf-8")
    original = source.read_bytes()
    saved_driver = mocker.Mock()
    saved_driver.page_source = '<a href="/survey?cursor=new">Next</a>'
    next_driver = mocker.Mock()
    next_driver.page_source = """
        <table><tbody>
        <tr><td>Stanford University</td><td>Computer Science<br>PhD</td>
            <td>Sep 20, 2026</td><td>Accepted</td>
            <td><a href="/result/101">Details</a></td></tr>
        <tr><td colspan="5">Fall 2026 American GPA 3.75</td></tr>
        </tbody></table>
    """
    chrome = mocker.patch.object(scrape.webdriver, "Chrome", side_effect=[saved_driver, next_driver])
    wait = mocker.patch.object(scrape, "WebDriverWait")
    if timeout:
        wait.return_value.until.side_effect = scrape.TimeoutException("Simulated timeout")
    save = mocker.spy(scrape, "save_data")

    scrape.main()

    saved_driver.get.assert_called_once_with(saved_url)
    saved_driver.quit.assert_called_once_with()
    if timeout:
        assert source.read_bytes() == original
        assert "Page load timed out. No new entries to save." in capsys.readouterr().out
        save.assert_not_called()
        assert chrome.call_count == 1
        next_driver.get.assert_not_called()
    else:
        next_driver.get.assert_called_once_with(next_url)
        next_driver.quit.assert_called_once_with()
        assert chrome.call_count == 2
        save.assert_called_once()
        stored = json.loads(source.read_text())
        assert len(stored) == 2
        assert stored[0] == existing[0]
        assert stored[1]["url"] == "https://www.thegradcafe.com/result/101"
        assert stored[1]["source_page_url"] == next_url
        assert stored[1]["program"] == "Computer Science"
        assert stored[1]["GPA"] == "3.75"


@pytest.mark.db
@pytest.mark.parametrize("failure_stage", ["connection", "query"])
def test_analysis_database_error(mocker, failure_stage):
    connect = mocker.patch.object(pages.Applicant, "connect_db")
    mocker.patch.object(pages, "Session")
    query = mocker.patch.object(pages.orm_queries, "fall_26_apps")
    error = SQLAlchemyError("Simulated database failure")
    if failure_stage == "connection":
        connect.side_effect = error
    else:
        query.side_effect = error

    app = create_app()
    app.config["TESTING"] = True
    log_exception = mocker.spy(app.logger, "exception")
    response = app.test_client().get("/")

    assert response.status_code == 503
    assert response.mimetype == "text/html"
    html = response.get_data(as_text=True)
    assert 'role="alert"' in html
    assert "Applicant data is unavailable. Please try again later." in html
    assert '<p class="value">' not in html
    log_exception.assert_called_once_with("Unable to load applicant analysis")
    if failure_stage == "query":
        connect.return_value.dispose.assert_called_once_with()
    else:
        query.assert_not_called()


@pytest.fixture()
def isolated_db_env(monkeypatch, tmp_path):
    # Run the real dotenv loader without reading or changing local credentials.
    monkeypatch.setattr(db_config, "__file__", str(tmp_path / "db_config.py"))
    names = {"DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT",
             "PYTHON_DOTENV_DISABLED"}
    monkeypatch.setattr(db_config.os, "environ", {
        key: value for key, value in db_config.os.environ.items() if key not in names
    })
    env_file = tmp_path / ".env"
    env_file.write_text(
        'DB_NAME=test_applicants\nDB_USER=test_user\n'
        'DB_PASSWORD="fake password"\nDB_HOST=localhost\nDB_PORT=5433\n',
        encoding="utf-8",
    )
    return env_file


@pytest.mark.db
def test_get_db_settings_loads_dotenv(isolated_db_env, mocker):
    loader = mocker.spy(db_config, "load_dotenv")

    assert db_config.get_db_settings() == {
        "db_name": "test_applicants", "db_user": "test_user",
        "db_password": "fake password", "db_host": "localhost", "db_port": 5433,
    }
    loader.assert_called_once_with(isolated_db_env)


@pytest.mark.db
def test_get_db_settings_prefers_environment(isolated_db_env, monkeypatch):
    monkeypatch.setenv("DB_NAME", "environment_database")
    monkeypatch.setenv("DB_PORT", "6543")
    settings = db_config.get_db_settings()
    assert settings["db_name"] == "environment_database"
    assert settings["db_port"] == 6543
    assert settings["db_user"] == "test_user"


@pytest.mark.db
def test_get_db_settings_reports_missing_values(isolated_db_env):
    isolated_db_env.write_text("DB_HOST=localhost\nDB_PORT=5432\n", encoding="utf-8")
    with pytest.raises(ValueError, match=(
        r"^Missing database settings: DB_NAME, DB_USER, DB_PASSWORD$"
    )):
        db_config.get_db_settings()


@pytest.mark.db
def test_get_db_settings_rejects_invalid_port(isolated_db_env, monkeypatch):
    monkeypatch.setenv("DB_PORT", "not-a-number")
    with pytest.raises(ValueError, match="invalid literal for int"):
        db_config.get_db_settings()


@pytest.mark.db
def test_stored_row_dictionary(mocker, tmp_path):
    record = {
        "university": "Example University", "program": "Computer Science",
        "comments": "Accepted with funding", "date_added": "Sep 20, 2026",
        "url": "https://example.com/applicants/1", "status": "Accepted",
        "term": "Fall 2026", "US/International": "American",
        "GPA": "3.75", "GRE": "325", "GRE V": "160", "GRE AW": "4.5",
        "Degree": "PhD", "llm-generated-program": "Computer Science",
        "llm-generated-university": "Example University",
    }
    source = tmp_path / "applicants.json"
    source.write_text(json.dumps([record]), encoding="utf-8")
    database = sqlite3.connect(":memory:")
    try:
        database.execute("""
            CREATE TABLE applicants (
                program TEXT, comments TEXT, date_added TEXT, url TEXT,
                status TEXT, term TEXT, us_or_international TEXT,
                gpa REAL, gre REAL, gre_v REAL, gre_aw REAL, degree TEXT,
                llm_generated_program TEXT, llm_generated_university TEXT
            )
        """)
        connection = mocker.MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.__iter__.side_effect = lambda: iter(
            database.execute("SELECT * FROM applicants").fetchall()
        )

        def insert_rows(statement, rows):
            # Adapt PostgreSQL placeholders and dates for the offline database.
            database.executemany(
                statement.as_string().replace("%s", "?"),
                [tuple(value.isoformat() if isinstance(value, date) else value
                       for value in row) for row in rows],
            )

        cursor.executemany.side_effect = insert_rows
        assert load_data(connection, file_path=source) == 1

        database.row_factory = sqlite3.Row
        stored = database.execute(
            "SELECT * FROM applicants WHERE url = ?", (record["url"],)
        ).fetchone()
        assert stored is not None
        assert dict(stored) == {
            "program": "Example University, Computer Science",
            "comments": "Accepted with funding", "date_added": "2026-09-20",
            "url": record["url"], "status": "Accepted", "term": "Fall 2026",
            "us_or_international": "American", "gpa": 3.75,
            "gre": 325.0, "gre_v": 160.0, "gre_aw": 4.5, "degree": "PhD",
            "llm_generated_program": "Computer Science",
            "llm_generated_university": "Example University",
        }
    finally:
        database.close()


@pytest.mark.db
@pytest.mark.parametrize("has_url", [True, False], ids=["with-url", "without-url"])
def test_repeated_pull_does_not_insert_duplicates(
    monkeypatch, mocker, tmp_path, insertion_db, has_url
):
    connection, cursor, rows = insertion_db
    monkeypatch.setattr(pages, "MODULE_DIR", tmp_path)
    records = [
        {
            "university": "Example University", "program": program,
            "url": f"https://example.com/applicants/{number}" if has_url else None,
            "term": "Fall 2026", "GPA": "3.75", "Degree": "PhD",
        }
        for number, program in enumerate(["Computer Science", "Mathematics"], start=1)
    ]
    # Also include duplicates within a single pull's input.
    payload = records + records
    inserted_counts = []

    def fake_run(command, **kwargs):
        script = Path(command[1]).name
        if script == "scrape.py":
            (tmp_path / "applicant_data.json").write_text(json.dumps(payload))
        elif script == "app.py":
            Path(command[command.index("--out") + 1]).write_text(json.dumps(payload))
        elif script == "load_data.py":
            inserted_counts.append(load_data(
                connection, file_path=command[command.index("--file-path") + 1]
            ))
        else:
            pytest.fail(f"Unexpected script: {script}")

    mocker.patch.object(pages.subprocess, "run", side_effect=fake_run)
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    assert rows == []

    first_response = client.post("/pull-data")
    assert first_response.status_code == 200
    assert first_response.get_json() == {"success": True}
    assert inserted_counts == [2]
    assert len(rows) == 2
    original_rows = list(rows)

    second_response = client.post("/pull-data")
    assert second_response.status_code == 200
    assert second_response.get_json() == {"success": True}
    assert inserted_counts == [2, 0]
    assert rows == original_rows
    assert cursor.executemany.call_args.args[1] == []

@pytest.fixture()
def insertion_db(mocker):
    # Simulate stored rows while exercising the real loader's transformations.
    rows = []
    connection = mocker.MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.__iter__.side_effect = lambda: iter(rows)

    def record_insert(statement, new_rows):
        assert "INSERT INTO" in statement.as_string()
        rows.extend(new_rows)

    cursor.executemany.side_effect = record_insert
    return connection, cursor, rows


@pytest.mark.db
def test_pull_data_inserts_rows(monkeypatch, mocker, tmp_path, insertion_db):
    connection, cursor, rows = insertion_db
    monkeypatch.setattr(pages, "MODULE_DIR", tmp_path)
    records = [
        {
            "university": "Example University", "program": "Computer Science",
            "comments": "Accepted with funding", "date_added": "Sep 20, 2026",
            "url": f"https://example.com/applicants/{number}",
            "status": "Accepted", "term": "Fall 2026",
            "US/International": "American", "GPA": "3.75",
            "GRE": "325", "GRE V": "160", "GRE AW": "4.5",
            "Degree": "PhD", "llm-generated-program": "Computer Science",
            "llm-generated-university": "Example University",
        }
        for number in (1, 2)
    ]
    inserted_counts = []

    def fake_run(command, **kwargs):
        script = Path(command[1]).name
        if script == "scrape.py":
            (tmp_path / "applicant_data.json").write_text(json.dumps(records))
        elif script == "app.py":
            output = Path(command[command.index("--out") + 1])
            output.write_text(json.dumps(records))
        elif script == "load_data.py":
            source = Path(command[command.index("--file-path") + 1])
            # Run the real loader with a fake database instead of a subprocess.
            inserted_counts.append(load_data(
                connection, table_name="applicants",
                file_path=source,
            ))
        else:
            pytest.fail(f"Unexpected script: {script}")

    mocker.patch.object(pages.subprocess, "run", side_effect=fake_run)
    assert rows == []
    cursor.executemany.assert_not_called()

    app = create_app()
    app.config["TESTING"] = True
    response = app.test_client().post("/pull-data")

    assert response.status_code == 200
    assert response.get_json() == {"success": True}
    assert inserted_counts == [2]
    cursor.executemany.assert_called_once()
    assert len(rows) == 2
    columns = (
        "program", "comments", "date_added", "url", "status", "term",
        "us_or_international", "gpa", "gre", "gre_v", "gre_aw", "degree",
        "llm_generated_program", "llm_generated_university",
    )
    for stored_row, record in zip(rows, records):
        row = dict(zip(columns, stored_row, strict=True))
        assert row == {
            "program": "Example University, Computer Science",
            "comments": "Accepted with funding", "date_added": date(2026, 9, 20),
            "url": record["url"], "status": "Accepted", "term": "Fall 2026",
            "us_or_international": "American", "gpa": 3.75,
            "gre": 325.0, "gre_v": 160.0, "gre_aw": 4.5, "degree": "PhD",
            "llm_generated_program": "Computer Science",
            "llm_generated_university": "Example University",
        }

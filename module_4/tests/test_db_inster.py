import json
import sqlite3
from datetime import date
from pathlib import Path

import pytest

from src import db_config
from src.board import create_app, pages
from src.load_data import load_data


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

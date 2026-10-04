import json
import re
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select

from src.board import create_app, pages
from src.load_data import load_data
from src.models import Base, Applicant


@pytest.fixture()
def integration_pipeline(monkeypatch, mocker, tmp_path):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    # The route disposes its engine after each request; retain this test database.
    real_dispose = engine.dispose
    mocker.patch.object(engine, "dispose")
    monkeypatch.setattr(pages, "MODULE_DIR", tmp_path)
    mocker.patch.object(pages.Applicant, "connect_db", return_value=engine)

    scraper = mocker.Mock()
    inserted_counts = []

    def fake_run(command, **kwargs):
        script = Path(command[1]).name
        if script == "scrape.py":
            (tmp_path / "applicant_data.json").write_text(json.dumps(scraper()))
        elif script == "app.py":
            source = Path(command[command.index("--file") + 1])
            enriched = json.loads(source.read_text())
            for record in enriched:
                record["llm-generated-program"] = record["program"]
                record["llm-generated-university"] = record["university"]
            Path(command[command.index("--out") + 1]).write_text(json.dumps(enriched))
        elif script == "load_data.py":
            raw = engine.raw_connection()
            try:
                connection = mocker.MagicMock()
                cursor = connection.cursor.return_value.__enter__.return_value
                # Schema exists already; PostgreSQL DDL and locks are mocked.
                cursor.__iter__.side_effect = lambda: iter(
                    tuple(date.fromisoformat(value) if index == 2 and value else value
                          for index, value in enumerate(row))
                    for row in raw.execute(
                    "SELECT program, comments, date_added, url, status, term, "
                    "us_or_international, gpa, gre, gre_v, gre_aw, degree, "
                    "llm_generated_program, llm_generated_university FROM applicants"
                ).fetchall())

                def insert_rows(statement, rows):
                    raw.executemany(
                        statement.as_string().replace("%s", "?"),
                        [tuple(value.isoformat() if isinstance(value, date) else value
                               for value in row) for row in rows],
                    )

                cursor.executemany.side_effect = insert_rows
                inserted_counts.append(load_data(
                    connection, file_path=command[command.index("--file-path") + 1]
                ))
                raw.commit()
            finally:
                raw.close()
        else:
            pytest.fail(f"Unexpected script: {script}")

    scripts = mocker.patch.object(pages.subprocess, "run", side_effect=fake_run)
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    try:
        yield client, engine, scraper, inserted_counts, scripts
    finally:
        real_dispose()


@pytest.mark.integration
@pytest.mark.parametrize("has_url", [True, False], ids=["with-url", "without-url"])
def test_overlapping_pulls_preserve_uniqueness(integration_pipeline, has_url):
    client, engine, scraper, inserted_counts, scripts = integration_pipeline
    records = [
        {
            "university": "Stanford University", "program": "Computer Science",
            "url": f"https://example.com/applicants/{number}" if has_url else None,
            "comments": f"Applicant {number}", "date_added": "Sep 20, 2026",
            "Degree": "PhD", "term": "Fall 2026", "status": "Accepted",
            "US/International": "American", "GPA": gpa, "GRE V": "160",
        }
        for number, gpa in enumerate(["3.5", "3.7", "3.9"], start=1)
    ]
    overlap = dict(records[1])
    if has_url:
        # URL is the identity: changed fields must not create or replace a row.
        overlap["GPA"] = "1.0"
    scraper.side_effect = [records[:2], [overlap, records[2], records[2]]]

    first = client.post("/pull-data")
    assert first.status_code == 200
    assert first.get_json() == {"success": True}
    with engine.connect() as db:
        before = db.execute(select(Applicant.__table__).order_by(Applicant.p_id)).mappings().all()
    assert len(before) == 2

    second = client.post("/pull-data")
    assert second.status_code == 200
    assert second.get_json() == {"success": True}
    assert inserted_counts == [2, 1]
    with engine.connect() as db:
        after = db.execute(select(Applicant.__table__).order_by(Applicant.p_id)).mappings().all()
    assert len(after) == 3
    assert after[:2] == before
    assert [row["comments"] for row in after] == [record["comments"] for record in records]
    assert [row["gpa"] for row in after] == [3.5, 3.7, 3.9]
    assert scraper.call_count == 2
    assert scripts.call_count == 6

    updated = client.get("/update-analysis")
    assert updated.status_code == 200
    assert re.findall(r'<p class="value">(.*?)</p>', updated.get_data(as_text=True)) == [
        "3", "3.70", "N/A", "3", "3", "100.00%"
    ]


@pytest.mark.integration
def test_pull_and_update_analysis_end_to_end(integration_pipeline):
    records = [
        {
            "university": "Stanford University", "program": "Computer Science",
            "url": f"https://example.com/applicants/{number}",
            "date_added": "Sep 20, 2026", "Degree": "PhD",
            "term": term, "status": status, "US/International": nationality,
            "GPA": gpa, "GRE V": gre_v,
        }
        for number, (term, status, nationality, gpa, gre_v) in enumerate([
            ("Fall 2026", "Accepted", "American", "3.7", "160"),
            ("Fall 2026", "Accepted", "American", "3.8", "165"),
            ("Fall 2026", "Rejected", "International", "4.0", None),
            ("Fall 2025", "Accepted", "American", "3.6", "155"),
            ("Fall 2025", "Accepted", "International", "3.9", "162"),
            ("Fall 2025", "Rejected", "American", "3.5", None),
        ], start=1)
    ]
    client, engine, scraper, inserted_counts, scripts = integration_pipeline
    scraper.return_value = records

    def rendered_values(response):
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert html.count('<h3 class="answer-label">Answer:</h3>') == 6
        return re.findall(r'<p class="value">(.*?)</p>', html)

    with engine.connect() as db:
        assert db.execute(select(Applicant.__table__)).all() == []
    assert rendered_values(client.get("/")) == ["0", "N/A", "N/A", "0", "0", "N/A"]

    pull = client.post("/pull-data")
    assert pull.status_code == 200
    assert pull.get_json() == {"success": True}
    scraper.assert_called_once_with()
    assert inserted_counts == [len(records)]
    with engine.connect() as db:
        stored = db.execute(select(Applicant.__table__).order_by(Applicant.url)).mappings().all()
    assert len(stored) == len(records)
    for row, record in zip(stored, records, strict=True):
        assert row["url"] == record["url"]
        assert row["program"] == "Stanford University, Computer Science"
        assert row["term"] == record["term"]
        assert row["status"] == record["status"]
        assert row["gpa"] == float(record["GPA"])
        assert row["llm_generated_program"] == record["program"]

    assert pages.pull_is_running() is False
    updated = client.get("/update-analysis")
    assert rendered_values(updated) == ["3", "3.75", "66.67%", "2", "2", "66.67%"]
    assert scripts.call_count == 3


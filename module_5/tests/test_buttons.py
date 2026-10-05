from pathlib import Path
import json
import sys
import subprocess
from datetime import date

from src import clean
from src.load_data import load_data
from src.board import create_app, pages
import pytest


@pytest.mark.buttons
@pytest.mark.parametrize("error", [
    subprocess.CalledProcessError(1, ["python", "scrape.py"]),
    OSError("Unable to start scraper"),
], ids=["script-failed", "os-error"])
def test_pull_data_failure(monkeypatch, mocker, tmp_path, error):
    monkeypatch.setattr(pages, "MODULE_DIR", tmp_path)
    mock_run = mocker.patch.object(pages.subprocess, "run", side_effect=error)
    app = create_app()
    app.config["TESTING"] = True
    log_exception = mocker.spy(app.logger, "exception")

    response = app.test_client().post("/pull-data")

    assert response.status_code == 500
    assert response.get_json() == {
        "error": "The data pull failed. Please try again."
    }
    log_exception.assert_called_once_with("Data pull failed")
    mock_run.assert_called_once()
    assert pages.pull_is_running() is False


@pytest.mark.buttons
def test_pull_data(monkeypatch, mocker, tmp_path):
    # scrape.py uses a direct import when launched as a script.
    monkeypatch.setitem(sys.modules, "clean", clean)
    from src import scrape

    # Keep the lock and generated files away from real application data.
    monkeypatch.setattr(pages, "MODULE_DIR", tmp_path)
    monkeypatch.setattr(clean, "__file__", str(tmp_path / "clean.py"))
    driver = mocker.Mock()
    driver.page_source = """
        <table><tbody>
        <tr><td>Stanford University</td><td>Computer Science<br>PhD</td>
            <td>Sep 20, 2026</td><td>Accepted on Sep 20, 2026</td>
            <td><a href="/result/101">Details</a></td></tr>
        <tr><td colspan="5">Fall 2026 American GPA 3.75 GRE V 160</td></tr>
        <tr><td>Georgetown University</td><td>Mathematics<br>Masters</td>
            <td>Sep 21, 2026</td><td>Rejected on Sep 21, 2026</td>
            <td><a href="/result/102">Details</a></td></tr>
        <tr><td colspan="5">Fall 2026 International GPA 3.50 GRE V 155</td></tr>
        </tbody></table>
    """
    mocker.patch.object(scrape.webdriver, "Chrome", return_value=driver)
    mocker.patch.object(scrape, "WebDriverWait").return_value.until.return_value = True
    cleaner = mocker.spy(scrape, "clean_data")
    connection = mocker.MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    stored_rows = []
    def selected_rows():
        params = cursor.execute.call_args.args[1]
        last_id = params[0] if len(params) == 2 else 0
        return iter([(index, *row) for index, row in enumerate(stored_rows, start=1)
                     if index > last_id][:params[-1]])

    cursor.__iter__.side_effect = selected_rows
    cursor.executemany.side_effect = lambda statement, rows: stored_rows.extend(rows)
    inserted_counts = []
    second_responses = []

    def fake_run(command, **kwargs):
        script = Path(command[1]).name
        if script == "scrape.py":
            # The first request still holds the lock while its scraper runs.
            # A second request raises BlockingIOError when acquiring that lock.
            if not second_responses:
                second_responses.append(None)
                second_responses[0] = app.test_client().post("/pull-data")
            scrape.main()
        elif script == "app.py":
            # Only LLM enrichment is simulated; retain the scraped field values.
            source = Path(command[command.index("--file") + 1])
            records = json.loads(source.read_text())
            for record in records:
                record["llm-generated-program"] = record["program"]
                record["llm-generated-university"] = record["university"]
            output = Path(command[command.index("--out") + 1])
            output.write_text(json.dumps(records), encoding="utf-8")
        elif script == "load_data.py":
            inserted_counts.append(load_data(
                connection, file_path=command[command.index("--file-path") + 1]
            ))
        else:
            pytest.fail(f"Unexpected script: {script}")

    mock_run = mocker.patch.object(pages.subprocess, "run", side_effect=fake_run)
    app = create_app()
    app.config["TESTING"] = True

    # Clicking Pull Data sends this POST request from the browser.
    response = app.test_client().post("/pull-data")

    assert response.status_code == 200
    assert response.get_json() == {"success": True}
    driver.get.assert_called_once_with("https://www.thegradcafe.com/survey")
    driver.quit.assert_called_once_with()
    cleaner.assert_called_once()
    cleaned = json.loads((tmp_path / "applicant_data.json").read_text())
    assert [record["GPA"] for record in cleaned] == ["3.75", "3.50"]
    assert inserted_counts == [2]
    assert stored_rows == [
        ("Stanford University, Computer Science", None, date(2026, 9, 20),
         "https://www.thegradcafe.com/result/101", "accepted", "Fall 2026",
         "American", 3.75, None, 160.0, None, "PhD", "Computer Science",
         "Stanford University"),
        ("Georgetown University, Mathematics", None, date(2026, 9, 21),
         "https://www.thegradcafe.com/result/102", "rejected", "Fall 2026",
         "International", 3.5, None, 155.0, None, "Masters", "Mathematics",
         "Georgetown University"),
    ]
    assert len(second_responses) == 1
    assert second_responses[0].status_code == 409
    assert second_responses[0].get_json() == {
        "error": "A data pull is already running. Please wait."
    }
    assert [Path(call.args[0][1]).name for call in mock_run.call_args_list] == [
        "scrape.py", "app.py", "load_data.py"
    ]


@pytest.mark.buttons
def test_busy_gating(monkeypatch, mocker, tmp_path):
    monkeypatch.setattr(pages, "MODULE_DIR", tmp_path)
    mock_connect = mocker.patch.object(pages.Applicant, "connect_db")
    mock_session = mocker.patch.object(pages, "Session")
    mock_queries = mocker.patch.object(pages, "orm_queries")
    mock_run = mocker.patch.object(pages.subprocess, "run")
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    # An active pull holds this exclusive lock until its work finishes.
    with (tmp_path / ".pull_data.lock").open("a") as lock:
        pages.fcntl.flock(lock, pages.fcntl.LOCK_EX | pages.fcntl.LOCK_NB)
        update_response = client.get("/update-analysis")
        pull_response = client.post("/pull-data")

    assert update_response.status_code == 409
    assert "Please update again after Pull Data finishes." in update_response.get_json()["error"]
    assert pull_response.status_code == 409
    assert pull_response.get_json() == {
        "error": "A data pull is already running. Please wait."
    }
    mock_connect.assert_not_called()
    mock_session.assert_not_called()
    assert mock_queries.mock_calls == []
    mock_run.assert_not_called()


@pytest.mark.buttons
def test_update_analysis(monkeypatch, mocker, tmp_path):
    monkeypatch.setattr(pages, "MODULE_DIR", tmp_path)
    mocker.patch.object(pages.Applicant, "connect_db")
    mock_session = mocker.patch.object(pages, "Session")
    session = mock_session.return_value.__enter__.return_value
    results = {
        "fall_26_apps": 12,
        "average_american_fall_26_gpa": 3.75,
        "percent_accepted_fall_25": 25.0,
        "accepted_fall_26_comp_sci_count": 4,
        "accepted_fall_26_llm_comp_sci_count": 3,
        "percent_reported_gre_v": 60.0,
    }
    queries = [
        mocker.patch.object(pages.orm_queries, name, return_value=value)
        for name, value in results.items()
    ]
    app = create_app()
    app.config["TESTING"] = True

    # Clicking Update Analysis sends this GET request from the browser.
    response = app.test_client().get("/update-analysis")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert '<div id="analysis-results">' in html
    assert '<p class="value">12</p>' in html
    assert '<p class="value">3.75</p>' in html
    for query in queries:
        query.assert_called_once_with(session)

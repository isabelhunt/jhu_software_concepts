from pathlib import Path
from src.board import create_app, pages
import pytest


@pytest.mark.buttons
def test_pull_data(monkeypatch, mocker, tmp_path):
    # Keep the lock and generated files away from real application data.
    monkeypatch.setattr(pages, "MODULE_DIR", tmp_path)
    second_responses = []

    def fake_run(command, **kwargs):
        if Path(command[1]).name == "scrape.py" and not second_responses:
            # The first request still holds the lock while its scraper runs.
            # A second request raises BlockingIOError when acquiring that lock.
            second_responses.append(None)
            second_responses[0] = app.test_client().post("/pull-data")
        # The route expects the enrichment script to create its output file.
        if "--out" in command:
            output = Path(command[command.index("--out") + 1])
            output.write_text("[]", encoding="utf-8")

    mock_run = mocker.patch.object(pages.subprocess, "run", side_effect=fake_run)
    app = create_app()
    app.config["TESTING"] = True

    # Clicking Pull Data sends this POST request from the browser.
    response = app.test_client().post("/pull-data")

    assert response.status_code == 200
    assert response.get_json() == {"success": True}
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
    mock_connect = mocker.patch.object(pages, "connect_db")
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
    mocker.patch.object(pages, "connect_db")
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

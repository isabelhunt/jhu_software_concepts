import re
import runpy
from pathlib import Path

import pytest
from flask import Flask 
from src.board.__init__ import create_app
from src import run
from src.board import pages

@pytest.mark.web
def test_create_app():
    app = create_app()
    assert app is not None
    assert isinstance(app, Flask)
    assert app.blueprints['pages'] is not None

    terminal_app_access = run.app
    assert terminal_app_access is not None
    assert isinstance(terminal_app_access, Flask)
    assert terminal_app_access.blueprints['pages'] is not None
    assert terminal_app_access.url_map.bind("localhost").match("/", method="GET") == ("pages.home", {})

@pytest.mark.web
def test_run_as_script(monkeypatch, mocker):
    run_path = Path(run.__file__).resolve()
    monkeypatch.syspath_prepend(str(run_path.parent))
    mock_run = mocker.patch.object(Flask, "run", autospec=True)
    namespace = runpy.run_path(str(run_path), run_name="__main__")
    app = namespace["app"]

    assert isinstance(app, Flask)
    assert app.blueprints["pages"] is not None
    mock_run.assert_called_once_with(app, host="localhost", port=8080, debug=True)


@pytest.fixture()
def app():
    app = create_app()
    app.config['TESTING'] = True
    yield app

@pytest.fixture()
def analysis_data(mocker):
    mocker.patch.object(pages, "connect_db")
    mocker.patch.object(pages, "Session")
    results = {
        "fall_26_apps": 12,
        "average_american_fall_26_gpa": 3.75,
        "percent_accepted_fall_25": 25.0,
        "accepted_fall_26_comp_sci_count": 4,
        "accepted_fall_26_llm_comp_sci_count": 3,
        "percent_reported_gre_v": 60.0,
    }
    for query, value in results.items():
        mocker.patch.object(pages.orm_queries, query, return_value=value)


@pytest.fixture()
def client(app, analysis_data):
    return app.test_client()

@pytest.fixture()
def runner(app):
    return app.test_cli_runner()

@pytest.mark.parametrize("page_name, expected_result",
    [
        ('/', 200),
    ])

@pytest.mark.web
def test_page_load(page_name, expected_result, client):
    response = client.get(page_name)
    assert response.status_code == expected_result
    html = response.get_data(as_text=True)
    assert '<button type="button" class="pull-data" id="pull-data" aria-describedby="pull-description">Pull Data</button>' in html
    assert '<button type="button" class="pull-data" id="update-analysis">Update Analysis</button>' in html


@pytest.mark.web
def test_analysis_and_answer_exist(client):
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    results = re.findall(r'<p class="value">(.*?)</p>', html, re.DOTALL)

    title = re.search(r"<title\b[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    assert title is not None, "Page is missing a <title> element"
    assert re.search(r"\banalysis\b", title.group(1), re.IGNORECASE), "Page title must include 'analysis'"

    assert any(
        re.fullmatch(r"\d+(?:\.\d+)?%?", result.strip())
        for result in results
    ), "Expected at least one question to display a numeric result"

import re

import pytest
from flask import Flask 
from src.board.__init__ import create_app
from src.board import pages

@pytest.mark.web
def test_create_app():
    app = create_app()
    assert app is not None
    assert type(app) == type(Flask(__name__))
    assert app.blueprints['pages'] is not None

@pytest.fixture()
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['LIVESERCER_PORT'] = 8080
    app.config['LIVESERVER_TIMEOUT'] = 10
    yield app

@pytest.fixture()
def client(app):
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
    title = re.search(r"<title\b[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    assert title is not None, "Page is missing a <title> element"
    assert re.search(r"\banalysis\b", title.group(1), re.IGNORECASE), "Page title must include 'analysis'"
    assert '<button type="button" class="pull-data" id="pull-data" aria-describedby="pull-description">Pull Data</button>' in html
    assert '<button type="button" class="pull-data" id="update-analysis">Update Analysis</button>' in html
    

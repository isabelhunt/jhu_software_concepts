from flask import Flask 
from src.board.__init__ import create_app

def test_create_app():

    app = create_app()

    assert app is not None

    assert type(app) == type(Flask(__name__))

    assert app.blueprints['pages'] is not None
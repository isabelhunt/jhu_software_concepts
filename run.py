"""Run the personal website locally."""

from pathlib import Path
import sys


MODULE_DIRECTORY = Path(__file__).resolve().parent / "Module 1"
sys.path.insert(0, str(MODULE_DIRECTORY))

from board import create_app


app = create_app()


if __name__ == "__main__":
    app.run(host="localhost", port=8080, debug=True)

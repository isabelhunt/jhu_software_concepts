import os
from pathlib import Path

from dotenv import load_dotenv


def get_db_settings():
    """Read local settings while respecting existing environment variables."""
    load_dotenv(Path(__file__).with_name(".env"))
    names = ("DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT")
    missing = [name for name in names if name not in os.environ]
    if missing:
        raise ValueError("Missing database settings: " + ", ".join(missing))
    return {
        "db_name": os.environ["DB_NAME"],
        "db_user": os.environ["DB_USER"],
        "db_password": os.environ["DB_PASSWORD"],
        "db_host": os.environ["DB_HOST"],
        "db_port": int(os.environ["DB_PORT"]),
    }

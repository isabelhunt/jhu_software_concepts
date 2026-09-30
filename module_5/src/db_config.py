import os
from pathlib import Path

from dotenv import load_dotenv


def get_db_settings():
    """Load database settings from the environment and the local dotenv file.

    Read ``.env`` beside this module without overriding existing environment
    variables.

    :returns: Settings keyed by ``db_name``, ``db_user``, ``db_password``,
        ``db_host``, and ``db_port``; the port is an integer.
    :rtype: dict[str, str or int]
    :raises ValueError: Required settings are missing or the port is not an integer.
    """
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

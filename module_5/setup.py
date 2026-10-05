"""Package the Module 5 Grad Cafe analytics application."""

from pathlib import Path

from setuptools import find_packages, setup


PROJECT_DIR = Path(__file__).resolve().parent
requirements = [
    line.strip()
    for line in (PROJECT_DIR / "requirements.txt").read_text(
        encoding="utf-8"
    ).splitlines()
    if line.strip() and not line.lstrip().startswith("#")
]

setup(
    name="grad-cafe-analytics",
    version="0.1.0",
    description="Collect and analyze graduate application results.",
    long_description=(PROJECT_DIR / "readme.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    author="Isabel Hunt",
    package_dir={"": "src"},
    packages=find_packages(where=str(PROJECT_DIR / "src")),
    py_modules=[
        "app",
        "clean",
        "db_config",
        "load_data",
        "models",
        "orm_queries",
        "query_data",
        "scrape",
    ],
    package_data={
        "board": [
            "templates/*.html",
            "templates/pages/*.html",
            "static/*.css",
        ],
    },
    install_requires=requirements,
)

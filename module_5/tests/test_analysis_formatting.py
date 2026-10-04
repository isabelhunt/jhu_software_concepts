import re
import sqlite3

import psycopg
from src import db_config, query_data
import pytest
from src.board import create_app, pages


@pytest.mark.analysis
def test_query_data_answers_all_questions(mocker, capsys):
    database = sqlite3.connect(":memory:")
    try:
        database.execute("""
            CREATE TABLE applicants (
                program TEXT, term TEXT, status TEXT, degree TEXT,
                us_or_international TEXT, gpa REAL, gre REAL, gre_v REAL,
                gre_aw REAL, llm_generated_program TEXT, llm_generated_university TEXT
            )
        """)
        database.executemany("INSERT INTO applicants VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [
            ("Stanford University, Computer Science", "Fall 2026", "Accepted", "PhD",
             "American", 3.0, 160, 150, 3, "Computer Science", "Stanford University"),
            ("MIT, CS", "Fall 2026", " accepted ", " phd ",
             " american ", 4.0, 170, 160, 4, "Computer Science", "MIT"),
            ("JHU, Computer Science", "Fall 2026", "Rejected", "Masters",
             "International", 3.5, None, 170, 5, "Computer Science", "Johns Hopkins University"),
            ("Temple University, Mathematics", "Fall 2025", "Accepted", "Masters",
             "International", 3.5, 150, None, None, "Mathematics", "Temple University"),
            ("Georgetown University, Computer Science", "Fall 2025", "Accepted", "PhD",
             "American", 4.0, None, None, None, "Computer Science", "Georgetown University"),
            ("Example University, Physics", "Fall 2025", "Rejected", "PhD",
             None, None, None, None, None, "Physics", "Example University"),
        ])
        connection = mocker.MagicMock()
        connection.__enter__.return_value = connection
        cursor = connection.cursor.return_value.__enter__.return_value
        sql_cursor = database.cursor()
        # Execute the actual SQL against fake records, without PostgreSQL.
        cursor.execute.side_effect = sql_cursor.execute
        cursor.fetchone.side_effect = sql_cursor.fetchone
        cursor.fetchall.side_effect = sql_cursor.fetchall
        connect = mocker.patch.object(psycopg, "connect", return_value=connection)
        mocker.patch.object(db_config, "get_db_settings", return_value={
            "db_name": "fake", "db_user": "fake", "db_password": "fake",
            "db_host": "localhost", "db_port": 5432,
        })

        db = query_data.create_connection(**db_config.get_db_settings())
        for query in (
            query_data.fall_26_apps, query_data.percent_international,
            query_data.average_stats, query_data.average_american_fall_26_gpa,
            query_data.percent_accepted_fall_25, query_data.average_accepted_fall_26_gpa,
            query_data.jhu_comp_sci_masters_count,
        ):
            query(db)
        original = query_data.accepted_fall_26_comp_sci_count(db)
        enriched = query_data.accepted_fall_26_llm_comp_sci_count(db)
        print(f"Difference: {original - enriched}")
        query_data.percent_reported_gre_v(db)
        query_data.temple_apps(db)

        assert capsys.readouterr().out.splitlines() == [
            "Connection to PostgreSQL DB successful",
            "Fall 2026 applicant count: 3",
            "Percent International: 40.00%",
            "Average GPA: 3.60",
            "Average GRE Quantitative: 160.00",
            "Average GRE Verbal: 160.00",
            "Average GRE Analytical Writing: 4.00",
            "Average GPA of American Fall 2026 applicants: 3.50",
            "Fall 2025 acceptance percentage: 66.67%",
            "Average GPA of accepted Fall 2026 applicants: 3.50",
            "Johns Hopkins Comp Sci Applicants: 1",
            "Original Field Count: 1",
            "llm Field Count: 2",
            "Difference: -1",
            "Percent reporting GRE verbal: 50.00%",
            "Temple University Applicant Count: 1",
        ]

        # A failed connection must print the error and return None.
        connect.side_effect = psycopg.OperationalError("Simulated connection failure")
        cursor.execute.reset_mock()
        assert query_data.create_connection(**db_config.get_db_settings()) is None
        assert capsys.readouterr().out.splitlines() == [
            "The error 'Simulated connection failure' occurred"
        ]
        cursor.execute.assert_not_called()
    finally:
        database.close()


@pytest.mark.analysis
def test_analysis_answer_labels(mocker):
    mocker.patch.object(pages.Applicant, "connect_db")
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

    app = create_app()
    app.config["TESTING"] = True
    response = app.test_client().get("/")

    html = response.get_data(as_text=True)
    articles = re.findall(r"<article\b[^>]*>(.*?)</article>", html, re.DOTALL)
    assert len(articles) == len(results)
    for article in articles:
        assert re.search(
            r'<h3 class="answer-label">\s*Answer:\s*</h3>\s*'
            r'<p class="value">\s*[^<\s][^<]*</p>',
            article,
        ), "Each analysis result must have an Answer: heading above its value"


@pytest.mark.analysis
@pytest.mark.parametrize("value, expected", [
    (3.756, "3.76"),
    (3.7, "3.70"),
    (0.0, "0.00"),
    (25.0, "25.00"),
])
def test_decimal_results_have_two_decimal_places(mocker, value, expected):
    mocker.patch.object(pages.Applicant, "connect_db")
    mocker.patch.object(pages, "Session")
    results = {
        "fall_26_apps": 12,
        "average_american_fall_26_gpa": value,
        "percent_accepted_fall_25": value,
        "accepted_fall_26_comp_sci_count": 4,
        "accepted_fall_26_llm_comp_sci_count": 3,
        "percent_reported_gre_v": value,
    }
    for query, result in results.items():
        mocker.patch.object(pages.orm_queries, query, return_value=result)

    app = create_app()
    app.config["TESTING"] = True
    response = app.test_client().get("/")
    values = re.findall(r'<p class="value">(.*?)</p>', response.get_data(as_text=True))
    assert values == ["12", expected, expected + "%", "4", "3", expected + "%"]
    for result in (values[1], values[2], values[5]):
        assert re.fullmatch(r"\d+\.\d{2}%?", result)

import re
import pytest
from src.board import create_app, pages


@pytest.mark.analysis
def test_analysis_answer_labels(mocker):
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
    mocker.patch.object(pages, "connect_db")
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

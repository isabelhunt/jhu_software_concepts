"""Data cleaning methods to be used in the scrape module

This module has methods clean_data, save_data, load_data, and 
jason_file_exists to be used withing the scrape.py module to 
aid in the scraping and storing of GradCafe data """

import re
import json
from pathlib import Path


def extract_details(detail_text):
    """Extract the application term and applicant origin.

    :param str detail_text: Combined text from a result's detail rows.
    :returns: Term and origin fields, with ``None`` for missing values.
    :rtype: dict[str, str | None]
    """
    entry = {}
    season_match = re.search(
        r"\b(?:Fall|Spring|Summer|Winter) \d{4}\b", detail_text
    )
    us_intl_match = re.search(
        r"\b(?:American|International|Other)\b", detail_text
    )
    entry["term"] = season_match.group() if season_match else None
    entry["US/International"] = (
        us_intl_match.group() if us_intl_match else None
    )
    return entry


def extract_decision(decision_text):
    """Extract the decision status and acceptance or rejection date.

    :param str decision_text: Text from the result's decision cell.
    :returns: Lowercase status and date fields. Missing dates are ``None``.
    :rtype: dict[str, str | None]
    :raises AttributeError: The text contains no recognized decision.
    """
    entry = {"accepted_date": None, "rejected_date": None}
    decision_match = re.search(
        r"\b(Accepted|Rejected|Wait listed|Interview|Pending)\b",
        decision_text,
        re.IGNORECASE,
    )
    decision_date_match = re.search(
        r"\bon\s+([A-Z][a-z]{2}\s+\d{1,2}(?:,\s*\d{4})?)\b",
        decision_text,
    )
    entry["status"] = decision_match.group(1).lower()
    if decision_match:
        if entry["status"] == "accepted" and decision_date_match:
            entry["accepted_date"] = decision_date_match.group(1)
        elif entry["status"] == "rejected" and decision_date_match:
            entry["rejected_date"] = decision_date_match.group(1)
    return entry


def extract_scores(detail_text):
    """Extract GRE and GPA fields, using ``None`` for missing scores.

    :param str detail_text: Combined text from a result's detail rows.
    :returns: GRE, GRE Q, GRE V, GRE AW, and GPA values as strings or ``None``.
    :rtype: dict[str, str | None]
    """
    entry = {}
    general_gre_match = re.search(
        r"\bGRE(?:\s+General)?\s*:?\s*(\d+(?:\.\d+)?)\b", detail_text
    )
    q_gre_match = re.search(
        r"\bGRE(?:,?\s+Q\b|,?\s+Quantitative)\s*:?\s*(\d+(?:\.\d+)?)\b",
        detail_text,
    )
    verbal_gre_match = re.search(
        r"\bGRE(?:,?\s+V\b|,?\s+Verbal)\s*:?\s*(\d+(?:\.\d+)?)\b",
        detail_text,
    )
    gpa_match = re.search(r"\bGPA\s*:?\s*(\d+(?:\.\d+)?)\b", detail_text)
    aw_gre_match = re.search(
        r"\bGRE(?:,?\s+AW\b|,?\s+Analytical Writing)"
        r"\s*:?\s*(\d+(?:\.\d+)?)\b",
        detail_text,
    )

    entry["GRE"] = general_gre_match.group(1) if general_gre_match else None
    entry["GRE Q"] = q_gre_match.group(1) if q_gre_match else None
    entry["GRE V"] = verbal_gre_match.group(1) if verbal_gre_match else None
    entry["GPA"] = gpa_match.group(1) if gpa_match else None
    entry["GRE AW"] = aw_gre_match.group(1) if aw_gre_match else None
    return entry


def clean_comments(detail_text):
    """Remove structured fields from the comment text.

    :param str detail_text: Combined text from a result's detail rows.
    :returns: Remaining comment text, or ``None`` if nothing remains.
    :rtype: str | None
    """
    comment_text = re.sub(
        r"\b(?:Accepted|Rejected|Wait listed|Interview) on "
        r"[A-Z][a-z]{2} \d{2}\b",
        "",
        detail_text,
    )
    comment_text = re.sub(
        r"\b(?:Fall|Spring|Summer|Winter) \d{4}\b", "", comment_text
    )
    comment_text = re.sub(
        r"\b(?:American|International|Other)\b", "", comment_text
    )
    comment_text = re.sub(
        r"\b(?:GRE(?:,?\s+(?:General|Q|Quantitative|V|Verbal|AW|"
        r"Analytical Writing))?|GPA)\s*:?\s*\d+(?:\.\d+)?\b",
        "",
        comment_text,
    )
    return comment_text.strip(" |, ") or None


def clean_data(soup, source_page_url):
    """Extract and normalize applicant records from survey HTML.

    :param soup: Parsed survey page containing result and detail rows.
    :type soup: bs4.BeautifulSoup
    :param str source_page_url: Survey page URL recorded on each result.
    :returns: Applicant dictionaries with extracted fields and source text.
    :rtype: list[dict]
    :raises AttributeError: A result row has no recognized decision.
    :raises TypeError: A result row has no result link.
    """
    entries = []
    rows = soup.find_all("tr")

    for index, row in enumerate(rows):
        cells = row.find_all("td", recursive=False)

        # A survey result has five table cells; this skips the heading row.
        if len(cells) != 5:
            continue

        details = []
        for detail_row in rows[index + 1:]:
            if len(detail_row.find_all("td", recursive=False)) == 5:
                break
            details.append(detail_row.get_text(" ", strip=True))

        detail_text = " ".join(details)
        raw_text = " ".join([row.get_text(" ", strip=True), *details])
        program_parts = cells[1].get_text("|", strip=True).split("|")
        result_link = row.find("a", href=re.compile(r"^/result/\d+"))
        result_url = f"https://www.thegradcafe.com{result_link['href']}"

        entry = {
            "program": program_parts[0] if program_parts else None,
            "university": cells[0].get_text(" ", strip=True) or None,
            "comments": None,
            "date_added": cells[2].get_text(" ", strip=True) or None,
            "url": result_url or None,
            "status": None,
            "accepted_date": None,
            "rejected_date": None,
            "term": None,
            "US/International": None,
            "GRE": None,
            "GRE V": None,
            "GRE Q": None,
            "GPA": None,
            "Degree": program_parts[1] if len(program_parts) > 1 else None,
            "GRE AW": None,
            "raw_text": raw_text or None,
            "source_page_url": source_page_url,
        }

        entry.update(extract_details(detail_text))
        entry.update(extract_decision(cells[3].get_text(" ", strip=True)))
        entry.update(extract_scores(detail_text))
        entry["comments"] = clean_comments(detail_text)

        entries.append(entry)

    return entries

def save_data(data):
    """Write applicant records to applicant_data.json beside this module.

    :param data: JSON-serializable applicant records to save.
    :type data: list[dict]
    :returns: None.
    :rtype: None
    :raises OSError: The output file cannot be written.
    :raises TypeError: A value cannot be serialized as JSON.
    """
    output_file = Path(__file__).with_name("applicant_data.json")
    with output_file.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

def load_data():
    """Read applicant_data.json from beside this module.

    :returns: The decoded applicant records.
    :rtype: list[dict]
    :raises OSError: The file cannot be read.
    :raises json.JSONDecodeError: The file does not contain valid JSON.
    """
    output_file = Path(__file__).with_name("applicant_data.json")
    with output_file.open("r", encoding="utf-8") as file:
        return json.load(file)

def json_file_exists():
    """Check whether applicant_data.json exists beside this module.

    :returns: Whether the data path exists.
    :rtype: bool
    """
    output_file = Path(__file__).with_name("applicant_data.json")
    return output_file.exists()

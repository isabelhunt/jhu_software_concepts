import re
import json
from pathlib import Path


def clean_data(soup):
    """Return soup as a list of dictionaries with cleaned field values."""
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
        program_parts = cells[1].get_text("|", strip=True).split("|")
        decision_text = cells[3].get_text(" ", strip=True)

        entry = {
            "program": program_parts[0] if program_parts else None,
            "university": cells[0].get_text(" ", strip=True) or None,
            "comments": None,
            "date_added": cells[2].get_text(" ", strip=True) or None,
            "url": None, #url with person ID
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
            "raw_text": detail_text or None,
            "source_page_url": None, #url of page
        }

        season_match = re.search(r"\b(?:Fall|Spring|Summer|Winter) \d{4}\b", detail_text)
        us_intl_match = re.search(r"\b(?:American|International|Other)\b", detail_text)
        decision_match = re.search(r"\b(Accepted|Rejected|Wait listed|Interview)\b", decision_text, re.IGNORECASE)
        decision_date_match = re.search(r"\bon\s+([A-Z][a-z]{2}\s+\d{1,2}(?:,\s*\d{4})?)\b", decision_text)
        general_gre_match = re.search(r"\bGRE(?:\s+General)?\s*:?\s*(\d+(?:\.\d+)?)\b", detail_text)
        q_gre_match = re.search(r"\bGRE(?:,?\s+Q\b|,?\s+Quantitative)\s*:?\s*(\d+(?:\.\d+)?)\b", detail_text)
        verbal_gre_match = re.search(r"\bGRE(?:,?\s+V\b|,?\s+Verbal)\s*:?\s*(\d+(?:\.\d+)?)\b", detail_text)
        gpa_match = re.search(r"\bGPA\s*:?\s*(\d+(?:\.\d+)?)\b", detail_text)
        aw_gre_match = re.search(r"\bGRE(?:,?\s+AW\b|,?\s+Analytical Writing)\s*:?\s*(\d+(?:\.\d+)?)\b", detail_text)

        entry["term"] = season_match.group() if season_match else None
        entry["US/International"] = us_intl_match.group() if us_intl_match else None
        entry["status"] = decision_match.group(1).lower()
        entry["GRE"] = general_gre_match.group(1) if general_gre_match else None
        entry["GRE Q"] = q_gre_match.group(1) if q_gre_match else None
        entry["GRE V"] = verbal_gre_match.group(1) if verbal_gre_match else None
        entry["GPA"] = gpa_match.group(1) if gpa_match else None
        entry["GRE AW"] = aw_gre_match.group(1) if aw_gre_match else None

        if decision_match:
            if entry["status"] == "accepted" and decision_date_match:
                entry["accepted_date"] = decision_date_match.group(1)
            elif entry["status"] == "rejected" and decision_date_match:
                entry["rejected_date"] = decision_date_match.group(1)
                
        comment_text = re.sub(r"\b(?:Accepted|Rejected|Wait listed|Interview) on [A-Z][a-z]{2} \d{2}\b", "", detail_text)
        comment_text = re.sub(r"\b(?:Fall|Spring|Summer|Winter) \d{4}\b", "", comment_text)
        comment_text = re.sub(r"\b(?:American|International|Other)\b", "", comment_text)
        comment_text = re.sub(r"\b(?:GRE(?:,?\s+(?:General|Q|Quantitative|V|Verbal|AW|Analytical Writing))?|GPA)\s*:?\s*\d+(?:\.\d+)?\b", "", comment_text)
        entry["comments"] = comment_text.strip(" |, ") or None

        entries.append(entry)

    return entries

def save_data(data):
    """Save entry data as JSON"""
    output_file = Path(__file__).with_name("applicant_data.json")
    with output_file.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

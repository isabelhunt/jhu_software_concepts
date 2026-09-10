from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
import re

url = "https://www.thegradcafe.com/survey"

# Use selenium to open the website 
driver = webdriver.Chrome()
driver.get(url)
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "tbody tr"))
)

# Parse the page HTML and store each page as an inner list.
soup = BeautifulSoup(driver.page_source, "html.parser")
html_storage = []
html_storage.append([soup.prettify()])

# Store each survey result as a dictionary.
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
    decision = cells[3].get_text(" ", strip=True) or None

    entry = {
        "program": program_parts[0] if program_parts else None,
        "school": cells[0].get_text(" ", strip=True) or None,
        "comments": None,
        "date_added": cells[2].get_text(" ", strip=True) or None,
        "decision": decision,
        "season_of_attendance": None,
        "status": None,
        "general_gre": None,
        "verbal_gre": None,
        "degree_type": program_parts[1] if len(program_parts) > 1 else None,
        "gpa": None,
        "aw_gre": None,
    }

    season_match = re.search(r"\b(?:Fall|Spring|Summer|Winter) \d{4}\b", detail_text)
    status_match = re.search(r"\b(?:American|International|Other)\b", detail_text)
    general_gre_match = re.search(r"\bGRE(?:,? (?:General|Quantitative))?\s*:?\s*(\d+(?:\.\d+)?)\b", detail_text)
    verbal_gre_match = re.search(r"\b(?:GRE )?(?:V|Verbal)\s*:?\s*(\d+(?:\.\d+)?)\b", detail_text)
    gpa_match = re.search(r"\bGPA\s*:?\s*(\d+(?:\.\d+)?)\b", detail_text)
    aw_gre_match = re.search(r"\b(?:GRE )?(?:AW|Analytical Writing)\s*:?\s*(\d+(?:\.\d+)?)\b", detail_text)

    entry["season_of_attendance"] = season_match.group() if season_match else None
    entry["status"] = status_match.group() if status_match else None
    entry["general_gre"] = general_gre_match.group(1) if general_gre_match else None
    entry["verbal_gre"] = verbal_gre_match.group(1) if verbal_gre_match else None
    entry["gpa"] = gpa_match.group(1) if gpa_match else None
    entry["aw_gre"] = aw_gre_match.group(1) if aw_gre_match else None

    comment_text = re.sub(r"\b(?:Accepted|Rejected|Wait listed|Interview) on [A-Z][a-z]{2} \d{2}\b", "", detail_text)
    comment_text = re.sub(r"\b(?:Fall|Spring|Summer|Winter) \d{4}\b", "", comment_text)
    comment_text = re.sub(r"\b(?:American|International|Other)\b", "", comment_text)
    comment_text = re.sub(r"\b(?:GRE(?:,? (?:General|Quantitative))?|GRE (?:V|AW)|Verbal|Analytical Writing|GPA)\s*:?\s*\d+(?:\.\d+)?\b", "", comment_text)
    entry["comments"] = comment_text.strip(" |, ") or None

    entries.append(entry)

print(entries)

# Close browser
driver.quit()

"""Data scraping and cleaning for GradeCafe data

This module provides the tools needed to scrape the GradeCafe main results
page and clean the data by importing the clean module.

This module utilizes the GradeCafeScraper class
"""

import time
from urllib.parse import urljoin

from selenium.webdriver.chrome.webdriver import WebDriver as Chrome
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup

from clean import clean_data, save_data, load_data, json_file_exists


class GradCafeScraper:
    """Scrape and clean a GradCafe survey page."""

    def __init__(self, url="https://www.thegradcafe.com/survey", num_of_records=30000):
        """Initialize the survey URL, Chrome driver, and HTML history.

        :param str url: Survey page URL to open.
        :returns: None.
        :rtype: None
        :raises selenium.common.exceptions.WebDriverException: Chrome cannot be started.
        """
        self.url = url
        self.driver = Chrome()
        self.entries = []
        self.num_of_records = num_of_records

    def _open(self):
        """Open the survey page and wait up to ten seconds for table rows.

        :returns: None.
        :rtype: None
        :raises selenium.common.exceptions.TimeoutException: No survey row appears in time.
        :raises selenium.common.exceptions.WebDriverException: Browser navigation fails.
        """
        self.driver.get(self.url)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "tbody tr"))
        )

    def scrape_data(self):
        """Collect pages and return records using one browser session."""
        try:
            while self.url and len(self.entries) < self.num_of_records:
                try:
                    soup = self.get_soup()
                except TimeoutException:
                    print("Page load timed out. Returning collected entries.")
                    break
                next_url = self.find_next_link(soup)
                self.entries.extend(clean_data(soup, self.url))
                self.url = next_url
            return self.entries
        finally:
            self.close()

    def get_soup(self):
        """Load and parse a page, allowing load errors to reach the caller."""
        self._open()
        return BeautifulSoup(self.driver.page_source, "html.parser")

    def find_next_link(self, soup):
        """Find the next cursor-based survey page.

        :param soup: Parsed page to search for a link labeled Next.
        :type soup: bs4.BeautifulSoup
        :returns: The absolute next-page URL, or ``None`` when no matching link exists.
        :rtype: str or None
        """
        next_url = next(
                    (
                        link
                        for link in soup.find_all("a", href=True)
                        if link.get_text(strip=True).lower() == "next" and "cursor=" in link["href"]
                    ),
                    None,
                )
        return urljoin(self.url, next_url["href"]) if next_url else None

    def close(self):
        """Quit Chrome and release the browser session.

        :returns: None.
        :rtype: None
        :raises selenium.common.exceptions.WebDriverException: The driver cannot quit.
        """
        self.driver.quit()

def main():
    """Collect, clean, and save survey records, resuming saved progress.

    Start with a target of 30,000 records, or resume after the last saved page
    with a target of 1,000 additional records. Stop when pagination ends or the
    target is reached. A resume-page timeout leaves the file unchanged; a timeout
    while collecting saves the records collected so far.

    :returns: None.
    :rtype: None
    :raises OSError: Saved records cannot be read or written.
    :raises json.JSONDecodeError: The existing data file is invalid JSON.
    :raises selenium.common.exceptions.WebDriverException: Browser operations fail
        with an error other than a handled page timeout.
    """
    start_time = time.perf_counter()

    entries = load_data() if json_file_exists() else []
    if entries:
        old_url = entries[-1].get("source_page_url")
        target = len(entries) + 1000
        last_scrape = GradCafeScraper(url=old_url, num_of_records=target)
        try:
            new_url = last_scrape.find_next_link(last_scrape.get_soup())
        except TimeoutException:
            print("Page load timed out. No new entries to save.")
            return
        finally:
            last_scrape.close()
        scraper = GradCafeScraper(url=new_url, num_of_records=target)
        scraper.entries = entries
        entries = scraper.scrape_data()
    else:
        scraper = GradCafeScraper()
        entries = scraper.scrape_data()

    save_data(entries)
    print(f'You have reached {len(entries)} records')
    end_time = time.perf_counter()
    print(f"Run time: {end_time - start_time}")

if __name__ == "__main__": # pragma: no cover
    main()

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
from clean import clean_data, save_data, load_data, _json_file_exists
from urllib.parse import urljoin
import time

class GradCafeScraper:
    """Scrape and clean a GradCafe survey page."""

    def __init__(self, url="https://www.thegradcafe.com/survey"):
        """Initialize the survey URL, Chrome driver, and HTML history.

        :param str url: Survey page URL to open.
        :returns: None.
        :rtype: None
        :raises selenium.common.exceptions.WebDriverException: Chrome cannot be started.
        """
        self.url = url
        self.driver = webdriver.Chrome()
        self.html_storage = []

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
        """Parse the current page and append its formatted HTML to the history.

        :returns: The parsed browser page source.
        :rtype: bs4.BeautifulSoup
        :raises selenium.common.exceptions.WebDriverException: Page source cannot be read.
        """
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        self.html_storage.append([soup.prettify()])
        return soup

    def _find_next_link(self, soup):
        """Find the next cursor-based survey page.

        :param soup: Parsed page to search for a link labeled Next.
        :type soup: bs4.BeautifulSoup
        :returns: The absolute next-page URL, or ``None`` when no matching link exists.
        :rtype: str or None
        """
        next_link = next(
            (
                link
                for link in soup.find_all("a", href=True)
                if link.get_text(strip=True).lower() == "next" and "cursor=" in link["href"]
            ),
            None,
        )
        return urljoin(self.url, next_link["href"]) if next_link else None

    def _close(self):
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
    :raises IndexError: The existing data file contains an empty list.
    :raises selenium.common.exceptions.WebDriverException: Browser operations fail
        with an error other than a handled page timeout.
    """
    url = "https://www.thegradcafe.com/survey"
    start_time = time.perf_counter()

    """Checks for existing json data"""
    if _json_file_exists():
        """Pulls existing data, finds the next url and continues"""
        entries = load_data()
        url = entries[-1].get("source_page_url", url)
        scraper = GradCafeScraper(url)
        try:
            scraper._open()
            soup = scraper.scrape_data()
            next_url = scraper._find_next_link(soup)
        except TimeoutException:
            print("Page load timed out. No new entries to save.")
            return
        finally:
            scraper._close()
        url = next_url
        num_of_records = len(entries) + 1000

    else:
        """If no existing data it starts with an empty list"""
        entries = []
        num_of_records = 30000

    while url and len(entries) < num_of_records:
        """Loop to grab fresh records until it hits num_of_records"""
        scraper = GradCafeScraper(url)
        try:
            scraper._open()
            soup = scraper.scrape_data()
            next_url = scraper._find_next_link(soup)
        except TimeoutException:
            print("Page load timed out. Saving collected entries.")
            save_data(entries)
            return
        finally:
            scraper._close()

        entries.extend(clean_data(soup, url))
        url = next_url

    """Saves scraped data to a json file"""
    save_data(entries)   
    print(f'You have reached {len(entries)} records')
    end_time = time.perf_counter()
    print(f"Run time: {end_time - start_time}")

"""
# uncomment to run directly in terminal
if __name__ == "__main__":
    main()
"""
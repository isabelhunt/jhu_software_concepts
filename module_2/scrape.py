from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
from clean import clean_data, save_data, load_data, _json_file_exists
from urllib.parse import urljoin
from pathlib import Path
import json
import time

class GradCafeScraper:
    """Scrape and clean a GradCafe survey page."""

    def __init__(self, url="https://www.thegradcafe.com/survey"):
        self.url = url
        self.driver = webdriver.Chrome()
        self.html_storage = []

    def _open(self):
        """Use Selenium to open the webpage in Chrome"""
        self.driver.get(self.url)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "tbody tr"))
        )
        
    def scrape_data(self):
        """Scrape soup object"""
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        self.html_storage.append([soup.prettify()])
        return soup

    def _find_next_link(self, soup):
        """Return the full URL for the Next survey page, if available."""
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
        """Close the browser"""
        self.driver.quit()

def main():
    url = "https://www.thegradcafe.com/survey"
    num_of_records = 30000
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
    else:
        """If no existing data it starts with an empty list"""
        entries = []

    while url and len(entries) < num_of_records:
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

    save_data(entries)   
    print(f'You have reached {len(entries)} records')
    end_time = time.perf_counter()
    print(f"Run time: {end_time - start_time}")

if __name__ == "__main__":
    main()

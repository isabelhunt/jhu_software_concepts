from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
from clean import clean_data, save_data
from urllib3.util import parse_url
from urllib.parse import urljoin
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
    start_time = time.perf_counter()
    scraper = GradCafeScraper(url)


    try:
        scraper._open()
        soup = scraper.scrape_data()

        next_url = scraper._find_next_link(soup)
        if next_url:
            print(f"Next link: {next_url}")
    finally:
        scraper._close()

    entries = clean_data(soup)
    save_data(entries)

    end_time = time.perf_counter()
    print(f"Run time: {end_time - start_time}")


if __name__ == "__main__":
    main()

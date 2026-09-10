from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
from clean import clean_data


class GradCafeScraper:
    """Scrape and clean the GradCafe survey page."""

    def __init__(self, url="https://www.thegradcafe.com/survey"):
        self.url = url
        self.driver = webdriver.Chrome()
        self.html_storage = []
        self.entries = []

    def scrape_data(self):
        """Open the survey page and return its cleaned entries."""
        self.driver.get(self.url)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "tbody tr"))
        )

        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        self.html_storage.append([soup.prettify()])
        self.entries = clean_data(soup)
        return self.entries

    def close(self):
        """Close the browser used by this scraper."""
        self.driver.quit()

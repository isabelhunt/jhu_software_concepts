from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup


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

    def _close(self):
        """Close the browser"""
        self.driver.quit()

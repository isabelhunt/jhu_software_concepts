from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
from clean import clean_data

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

# Store each survey result as a cleaned dictionary.
entries = clean_data(soup)

print(entries)

# Close browser
driver.quit()

from selenium import webdriver
import time

url = "https://www.thegradcafe.com/survey"

# Use selenium to open the website 
driver = webdriver.Chrome()
driver.get(url)

# Wait and close browser
time.sleep(3)
driver.quit()


Isabel Hunt (ihunt5)
Module 2 Assignment: Web Scraping due on September 13th @11:59 pm

### SSH to the github repo ###
git@github.com:isabelhunt/jhu_software_concepts.git

### Robots.txt Check ###
robots.txt for https://www.thegradcafe.com/ declares that all users-agents 
can search the website, ai can reference the content, but not use it to 
train ai. This codebase accesses the site's content, parses it, and uses an
LLM to clean it. This codebase does not access restricted areas or use the 
content to train an LLM. 

### To run scraper ###
in your venv run:
pip install -r requirements.txt

This code scrapes 30,000 entries, if you require a different amount:
open scrape.py and edit line 50 for the desired number of entries to be scraped. 
Note that this represents the total number of entries if some already exist. 

in your venv run:
python scrape.py

### Notes on Approach ###
This project uses a combination of Selenium and BeautifulSoup to scrape data. 
The class GradCafeScraper uses two private functions; _open() and _close() which
utilizes Selenium's implicit wait feature so that pages are opened and closed as
quickly as possible while still allowing for data to be scraped. 
The scrape_data() functions utilizes BeautifulSoup to grab the open webpage html
and returns a soup object. This combination is desired becuse Selenium opens a 
real browser page which renders the full website's html allowing us to grab the 
"Next" button's url which ultimately enables us to navigate through new entires. 
Selenium renders the page using Chrome and Chrome driver BeuatifulSoup creates a
much cleaner text block that is able to be parsed with regex logic that is 
housed in the clean() function.

### Known bugs ###
Attempted logic in the main() loop to save progress if Selenium throws a time 
out error but this never actually worked in practice. I found that I could 
run ~5,000 entires at a time and the more I tried to parse at once it would 
crash but not save the data, I found it easier to just run it piece meal then 
mess with that code because I was going to have to run it pice by piece anyways. 



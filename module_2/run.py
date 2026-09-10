from scrape import GradCafeScraper
from clean import clean_data


def main():
    scraper = GradCafeScraper()
    try:
        soup = scraper.scrape_data()
        entries = clean_data(soup)
        print(entries)
    finally:
        scraper.close()


if __name__ == "__main__":
    main()

from scrape import GradCafeScraper
from clean import clean_data, save_data
import time

def main():
    start_time = time.perf_counter()
    scraper = GradCafeScraper()
    try:
        scraper._open()
        soup = scraper.scrape_data()
    finally:
        scraper._close()

    entries = clean_data(soup)
    save_data(entries)

    end_time = time.perf_counter()
    print(f"Run time: {end_time - start_time}")


if __name__ == "__main__":
    main()

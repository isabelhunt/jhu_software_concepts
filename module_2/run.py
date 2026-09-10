from scrape import GradCafeScraper


def main():
    scraper = GradCafeScraper()
    try:
        entries = scraper.scrape_data()
        print(entries)
    finally:
        scraper.close()


if __name__ == "__main__":
    main()

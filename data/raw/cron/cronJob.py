import psycopg2
import csv
import os
from datetime import datetime
from utils.db import get_db_connection
from scrapy.crawler import CrawlerProcess
from masothue.spiders.link_spider import LinkSpider

SUMMARY_CSV = "output/summary_success_rate.csv"
NEW_TAXCODES_CSV = "output/new_taxcodes.csv"

def summarize_field_success_rate():
    print("Summarizing field success rate...")
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM company_tax_info")
    rows = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]

    field_total = len(rows)
    field_counts = {field: 0 for field in colnames}

    for row in rows:
        for i, value in enumerate(row):
            if value not in (None, '', 'N/A'):
                field_counts[colnames[i]] += 1

    # Ghi CSV
    os.makedirs("output", exist_ok=True)
    with open(SUMMARY_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Field", "Non-Empty Count", "Total Rows", "Success Rate (%)"])
        for field, count in field_counts.items():
            percent = (count / field_total) * 100 if field_total > 0 else 0
            writer.writerow([field, count, field_total, f"{percent:.2f}"])

    print(f"Field summary saved to {SUMMARY_CSV}")

    cur.close()
    conn.close()

def check_for_new_taxcodes_and_update():
    print("\nChecking for new taxcodes from masothue.com...")
    from masothue.items import CompanyLinkItem
    from scrapy import signals
    from pydispatch import dispatcher

    new_taxcodes = []
    existing_taxcodes = set()

    # Load existing taxcodes from DB
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT tax_code FROM company_tax_link")
    for row in cur.fetchall():
        existing_taxcodes.add(row[0])
    cur.close()
    conn.close()

    def collect_new_links(item, response, spider):
        if isinstance(item, CompanyLinkItem):
            tax_code = item['tax_code']
            if tax_code not in existing_taxcodes:
                new_taxcodes.append({
                    "tax_code": tax_code,
                    "href": item['href']
                })

    dispatcher.connect(collect_new_links, signal=signals.item_passed)

    process = CrawlerProcess(settings={
        'USER_AGENT': 'Mozilla/5.0',
        'LOG_ENABLED': False,
    })

    process.crawl(LinkSpider)
    process.start()

    # Ghi các taxcode mới ra CSV
    if new_taxcodes:
        with open(NEW_TAXCODES_CSV, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["tax_code", "href"])
            writer.writeheader()
            writer.writerows(new_taxcodes)
        print(f"Found {len(new_taxcodes)} new taxcodes. Saved to {NEW_TAXCODES_CSV}")
    else:
        print("No new taxcodes found.")

if __name__ == "__main__":
    summarize_field_success_rate()
    check_for_new_taxcodes_and_update()

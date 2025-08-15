import datetime
import psycopg2
from utils.db import get_db_connection

class PostgresPipeline:
    def open_spider(self, spider):
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()
    
    def close_spider(self, spider):
        self.cursor.close()
        self.conn.commit()
        self.conn.close()
    
    def process_item(self, item, spider):
        try:
            if spider.name == "link_spider":
                self.cursor.execute(
                    """
                    INSERT INTO company_tax_link (href)
                    VALUES (%s)
                    ON CONFLICT DO NOTHING
                    """,
                    (item['href'],)
                )
            elif spider.name == "detail_worker_spider":
                self.cursor.execute(
                    """
                    INSERT INTO company_tax_info (
                        tax_code, company_name, address, status, representative,
                        phone, start_date, managed_by, last_updated
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (tax_code) DO NOTHING
                    """,
                    (
                        item['tax_code'], item['company_name'], item['address'], item['status'],
                        item['representative'], item['phone'], item['start_date'],
                        item['managed_by'], datetime.datetime.now()
                    )
                )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback() 
            spider.logger.error(f"[PostgresPipeline] DB error: {e}")
        return item

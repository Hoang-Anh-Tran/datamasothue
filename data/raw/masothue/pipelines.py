import datetime
import psycopg2
from utils.db import get_db_connection 
import json

class PostgresPipeline:
    def open_spider(self, spider):
        """Được gọi khi spider bắt đầu chạy"""
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()

    def close_spider(self, spider):
        """Được gọi khi spider kết thúc"""
        self.cursor.close()
        self.conn.commit()
        self.conn.close()

    def process_item(self, item, spider):
        try:
            if spider.name == "detail_worker_spider":
                self.cursor.execute(
                    """
                    INSERT INTO company_tax_info_table (tax_code, data)
                    VALUES (%s, %s)
                    ON CONFLICT (tax_code) DO NOTHING
                    """,
                    (
                        item['tax_code'],
                        json.dumps(dict(item))  
                    )
                )
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            spider.logger.error(f"[PostgresPipeline] DB error: {e}")
        return item

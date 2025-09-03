import scrapy
import psycopg2
import os
import redis
import time
from dotenv import load_dotenv
from utils.db import get_db_connection

load_dotenv()

class JsonParserSpider(scrapy.Spider):
    name = "json_parser_spider"
    custom_settings = {
        "LOG_LEVEL": "INFO"
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.starttime = time.time()

        # PostgreSQL
        self.conn = get_db_connection()
        self.conn.autocommit = True
        self.cur = self.conn.cursor()

        # Đảm bảo bảng parsed tồn tại
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS company_tax_parsed (
            tax_id TEXT PRIMARY KEY
        );
        """)

        # Redis
        self.redis_conn = redis.StrictRedis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True
        )

    def start_requests(self):
        """Không crawl web, chỉ parse dữ liệu JSONB trong DB"""
        self.logger.info("[*] Bắt đầu parse dữ liệu JSONB từ company_tax_info_table...")

        self.cur.execute("SELECT tax_code, data FROM company_tax_info_table;")
        rows = self.cur.fetchall()

        for tax_code, data in rows:
            self.parse_record(tax_code, data)

    def parse_record(self, tax_code, data):
        conn = get_db_connection()
        cur = conn.cursor()

        # Insert trước nếu chưa có tax_id
        cur.execute("""
            INSERT INTO company_tax_parsed (tax_id) VALUES (%s)
            ON CONFLICT (tax_id) DO NOTHING;
        """, (tax_code,))

        if isinstance(data, dict):
            for key, val in data.items():
                self.handle_key_value(cur, tax_code, key, val)

        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    for key, val in item.items():
                        self.handle_key_value(cur, tax_code, key, val)
                else:
                    # Nếu là value thô thì lưu vào cột đặc biệt
                    self.handle_key_value(cur, tax_code, "list_value", item)

        conn.commit()
        cur.close()
        conn.close()

        # Push vào Redis queue
        self.redis_conn.rpush("parsed_queue", tax_code)
        self.logger.info(f"[QUEUE] Đẩy vào Redis queue: {tax_code}")

    def handle_key_value(self, cur, tax_code, key, val):
        # Đảm bảo cột tồn tại trong company_tax_parsed
        cur.execute(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = 'company_tax_parsed'
                    AND column_name = %s
                ) THEN
                    EXECUTE 'ALTER TABLE company_tax_parsed ADD COLUMN "' || %s || '" TEXT';
                END IF;
            END
            $$;
        """, (key, key))

        # Cập nhật dữ liệu
        cur.execute(
            f'UPDATE company_tax_parsed SET "{key}" = %s WHERE tax_id = %s;',
            (str(val), tax_code)
        )

    def closed(self, reason):
        self.cur.close()
        self.conn.close()
        self.logger.info(f"[DONE] Spider dừng với lý do: {reason}")

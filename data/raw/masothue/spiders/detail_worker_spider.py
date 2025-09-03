import scrapy
import redis
import re
from masothue.items import CompanyDetailItem
from utils.db import get_db_connection
import os
from dotenv import load_dotenv
from datetime import datetime
import psycopg2
import pandas as pd
import json
import numpy as np
import io
import time

load_dotenv()

class DetailWorkerSpider(scrapy.Spider):
    name = "detail_worker_spider"
    handle_httpstatus_list = [403, 407]
    table_name = "company_details"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.starttime = time.time()

        self.redis_conn = redis.StrictRedis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True
        )

    def start_requests(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT tax_id, href FROM company_tax_link_4")
        results = cursor.fetchall()
        conn.close()

        if not results:
            self.logger.info("Không tìm thấy mã số thuế nào trong bảng company_tax_link_4.")
            return

        for tax_id, href in results:
            key = f"tax:{tax_id}"
            if self.redis_conn.exists(key):
                self.logger.info(f"[SKIP] {tax_id} đã được crawl trước đó")
                continue

            self.logger.info(f"Worker đang xử lý mã số thuế: {tax_id}")
            yield scrapy.Request(
                url=href,
                callback=self.parse_detail,
                meta={"tax_code": tax_id}
            )

    def parse_detail(self, response):
        tax_id = response.meta.get("tax_code")
        try:
            data = pd.read_html(io.StringIO(response.text))[0]
            data.columns = ['key', 'value']
            data = data.replace({np.nan:None})
            data = data.to_dict(orient="records")

            self.redis_conn.set(f"tax:{tax_id}", 1)  # Đánh dấu đã crawl

            self.upsert_data(data,tax_id)
        
        except Exception as e:
            self.logger.error(f"[!] Lỗi khi parse dữ liệu cho {tax_id}: {e}")
            return

    def upsert_data(self, data, tax_code):
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            INSERT INTO company_tax_info_table (tax_code, data)
            VALUES (%s, %s)
            ON CONFLICT (tax_code) DO NOTHING
        """
        cursor.execute(sql, (tax_code, json.dumps(data)))
        conn.commit()
        conn.close()
        elapsed = time.time() - self.starttime
        self.logger.info(f"[TIMER] Request xử lý hết {elapsed:.2f} giây")

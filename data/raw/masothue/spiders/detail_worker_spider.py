# import scrapy
# import redis
# import re
# from masothue.items import CompanyDetailItem
# from utils.db import get_db_connection
# import os
# from dotenv import load_dotenv
# from datetime import datetime

# load_dotenv()

# class DetailWorkerSpider(scrapy.Spider):
#     name = "detail_worker_spider"
#     handle_httpstatus_list = [403, 407]

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         # Kết nối Redis
#         self.redis_conn = redis.StrictRedis(
#             host=os.getenv("REDIS_HOST", "localhost"),
#             port=int(os.getenv("REDIS_PORT", 6379)),
#             db=int(os.getenv("REDIS_DB", 0)),
#             decode_responses=True
#         )

#     def start_requests(self):
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute("SELECT tax_id, href FROM company_tax_link_4")
#         results = cursor.fetchall()
#         conn.close()

#         if not results:
#             self.logger.info("Không tìm thấy mã số thuế nào trong bảng company_tax_link_4.")
#             return

#         for tax_id, href in results:
#             key = f"tax:{tax_id}"
#             if self.redis_conn.exists(key):
#                 self.logger.info(f"[SKIP] {tax_id} đã được crawl trước đó")
#                 continue

#             self.logger.info(f"Worker đang xử lý mã số thuế: {tax_id}")
#             yield scrapy.Request(
#                 url=href,
#                 callback=self.parse_detail,
#                 meta={"tax_code": tax_id}
#             )

#     def parse_detail(self, response):
#         tax_id = response.meta.get("tax_code")

#         if response.status in [403, 407]:
#             self.logger.warning(f"[!] Proxy bị từ chối ({response.status}): {response.url}")
#             return

#         def extract_xpath(path, default=""):
#             result = response.xpath(path).get()
#             return result.strip() if result else default

#         def extract_last_address_xpath():
#             addresses = response.xpath('//td[@itemprop="address"]/span[@class="copy"]/text()').getall()
#             return addresses[-1].strip() if addresses else ""

#         def extract_by_label_xpath(label):
#             return response.xpath(
#                 f'//tr[td[contains(text(), "{label}")]]/td[2]//text()'
#             ).get(default='').strip()

#         def extract_last_updated_xpath():
#             raw_text = response.xpath(
#                 '//td[contains(.//text(), "Cập nhật mã số thuế")]//em/text()'
#             ).get()
#             if not raw_text:
#                 return None
#             raw_text = raw_text.strip()

#             # Thử nhiều format ngày
#             for fmt in ("%d/%m/%Y", "%d/%m/%Y %H:%M", "%d-%m-%Y", "%d-%m-%Y %H:%M:%S"):
#                 try:
#                     return datetime.strptime(raw_text, fmt)
#                 except ValueError:
#                     continue
#             self.logger.warning(f"[!] Không parse được ngày: {raw_text}")
#             return None

#         company_name = extract_xpath('//th[@itemprop="name"]/span[@class="copy"]/text()')
#         tax_code = extract_xpath('//td[@itemprop="taxID"]/span[@class="copy"]/text()')
#         address = extract_last_address_xpath()
#         status = extract_by_label_xpath("Tình trạng")
#         representative = extract_xpath('//tr[@itemprop="alumni"]//span[@itemprop="name"]/a/text()')
#         phone = extract_xpath('//td[@itemprop="telephone"]/span[@class="copy"]/text()')
#         start_date = extract_by_label_xpath("Ngày hoạt động")
#         managed_by = extract_by_label_xpath("Quản lý bởi")
#         last_updated = extract_last_updated_xpath()

#         # Đánh dấu đã crawl
#         if tax_code and company_name:
#             self.redis_conn.set(f"tax:{tax_code}", 1)
#         else:
#             self.logger.warning(f"Bỏ qua đánh dấu vì dữ liệu rỗng cho {tax_code}")

#         yield CompanyDetailItem(
#             tax_code=tax_code,
#             company_name=company_name,
#             address=address,
#             status=status,
#             representative=representative,
#             phone=phone,
#             start_date=start_date,
#             managed_by=managed_by,
#             last_updated=last_updated
#         )


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

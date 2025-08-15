import scrapy
from masothue.items import CompanyDetailItem
from utils.redis_queue import pop_taxcode
from utils.db import get_db_connection
import os
from dotenv import load_dotenv

load_dotenv()

class DetailWorkerSpider(scrapy.Spider):
    name = "detail_worker_spider"

    def start_requests(self):
        queue_name = os.getenv("REDIS_QUEUE")
        taxcode = pop_taxcode(queue_name)
        if not taxcode:
            self.logger.info("Không có mã số thuế trong hàng đợi.")
            return
        taxcode = taxcode.decode()
        self.logger.info(f"Worker đang xử lý mã số thuế: {taxcode}")

        # Lấy URL từ DB dựa theo tax_code
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT href FROM company_tax_link WHERE tax_code = %s", (taxcode,))
        result = cursor.fetchone()
        conn.close()

        if result:
            yield scrapy.Request(url=result[0], callback=self.parse_detail, meta={"tax_code": taxcode})
        else:
            self.logger.warning(f"Không tìm thấy link tương ứng cho mã số thuế: {taxcode}")

    def parse_detail(self, response):
        def extract_text(selector):
            return response.css(selector).get(default="").strip()

        yield CompanyDetailItem(
            tax_code=response.meta["tax_code"],
            company_name=extract_text("h1::text"),
            address=extract_text(".company-detail .table tr:nth-child(2) td::text"),
            status=extract_text(".company-detail .table tr:nth-child(3) td::text"),
            representative=extract_text(".company-detail .table tr:nth-child(4) td::text"),
            phone=extract_text(".company-detail .table tr:nth-child(5) td::text"),
            start_date=extract_text(".company-detail .table tr:nth-child(6) td::text"),
            managed_by=extract_text(".company-detail .table tr:nth-child(7) td::text"),
        )
# import scrapy
# import re

# class MasothueLinkSpider(scrapy.Spider):
#     name = "link_spider"
#     allowed_domains = ["masothue.com"]
#     start_urls = ["https://masothue.com/tra-cuu-ma-so-thue-theo-tinh"]

#     def parse(self, response):
#         # Bắt đầu từ cấp tỉnh/thành phố
#         location_links = response.css('a[href^="/tra-cuu-ma-so-thue-theo-tinh/"]::attr(href)').getall()
#         for link in location_links:
#             full_link = response.urljoin(link)
#             yield scrapy.Request(
#                 full_link,
#                 callback=self.parse_location,
#                 meta={"page": 1}
#             )

#     def parse_location(self, response):
#         page = response.meta.get("page", 1)

#         # Crawl tất cả link công ty nếu có
#         company_links = [
#             link for link in response.css('a[href^="/"]::attr(href)').getall()
#             if re.match(r"^/\d{8,}-", link)
#         ]

#         for link in company_links:
#             full_url = response.urljoin(link)
#             match = re.search(r"/(\d{8,}(?:-\d{3})?)-", link)
#             tax_id = match.group(1) if match else None

#             if tax_id:
#                 yield {
#                     "tax_id": tax_id,
#                     "href": full_url,
#                 }

#         # Nếu có phân trang (số trang dạng ?page=), tiếp tục crawl trang sau
#         pagination_links = response.css('ul.pagination li a::attr(href)').getall()
#         next_pages = [link for link in pagination_links if f"?page={page + 1}" in link]

#         if next_pages:
#             next_url = response.urljoin(next_pages[0])
#             yield scrapy.Request(
#                 url=next_url,
#                 callback=self.parse_location,
#                 meta={"page": page + 1}
#             )
#         else:
#             # Không còn trang tiếp theo -> kiểm tra xem có sub-location không
#             sub_location_links = response.css('a[href^="/tra-cuu-ma-so-thue-theo-tinh/"]::attr(href)').getall()
#             for link in sub_location_links:
#                 full_link = response.urljoin(link)
#                 yield scrapy.Request(
#                     full_link,
#                     callback=self.parse_location,
#                     meta={"page": 1}
#                 )


import scrapy
import re
import redis
import os
from dotenv import load_dotenv

load_dotenv()

class MasothueLinkSpider(scrapy.Spider):
    name = "link_spider"
    allowed_domains = ["masothue.com"]
    start_urls = ["https://masothue.com/tra-cuu-ma-so-thue-theo-tinh"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.redis_conn = redis.StrictRedis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True
        )

    def parse(self, response):
        location_links = response.css('a[href^="/tra-cuu-ma-so-thue-theo-tinh/"]::attr(href)').getall()
        for link in location_links:
            full_link = response.urljoin(link)
            yield scrapy.Request(
                full_link,
                callback=self.parse_location,
                meta={"page": 1}
            )

    def parse_location(self, response):
        page = response.meta.get("page", 1)

        
        company_links = [
            link for link in response.css('a[href^="/"]::attr(href)').getall()
            if re.match(r"^/\d{8,}-", link)
        ]

        for link in company_links:
            full_url = response.urljoin(link)
            match = re.search(r"/(\d{8,}(?:-\d{3})?)-", link)
            tax_id = match.group(1) if match else None

            if tax_id:
                redis_key = f"tax:{tax_id}"
                if not self.redis_conn.exists(redis_key):
                    self.redis_conn.rpush("link_queue", full_url)
                    self.redis_conn.set(redis_key, 0)  # 0 = chưa crawl
                    self.logger.info(f"[QUEUE] Thêm vào hàng đợi: {tax_id}")
                else:
                    self.logger.info(f"[SKIP] Đã tồn tại: {tax_id}")

        pagination_links = response.css('ul.pagination li a::attr(href)').getall()
        next_pages = [link for link in pagination_links if f"?page={page + 1}" in link]

        if next_pages:
            next_url = response.urljoin(next_pages[0])
            yield scrapy.Request(
                url=next_url,
                callback=self.parse_location,
                meta={"page": page + 1}
            )
        else:
            sub_location_links = response.css('a[href^="/tra-cuu-ma-so-thue-theo-tinh/"]::attr(href)').getall()
            for link in sub_location_links:
                full_link = response.urljoin(link)
                yield scrapy.Request(
                    full_link,
                    callback=self.parse_location,
                    meta={"page": 1}
                )



# import scrapy
# from masothue.items import CompanyLinkItem

# class LinkSpider(scrapy.Spider):
#     name = "link_spider"
#     allowed_domains = ["tratencongty.com"]
#     start_urls = [f"https://tratencongty.com/?page={i}" for i in range(1, 38142)]

#     def parse(self, response):
#         links = response.css("a[href^='/company/']::attr(href)").getall()
#         for link in links:
#             full_url = response.urljoin(link)
#             yield CompanyLinkItem(href=full_url)

# masothue/spiders/link_spider.py

import scrapy
from scrapy_splash import SplashRequest
from masothue.items import CompanyLinkItem

class LinkSpider(scrapy.Spider):
    name = "link_spider"
    allowed_domains = ["tratencongty.com"]
    start_urls = [f"https://tratencongty.com/?page={i}" for i in range(5737, 38142)]

    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(
                url,
                self.parse,
                args={"wait": 2},  # thời gian đợi JavaScript render
            )

    def parse(self, response):
        links = response.css("a[href*='/company/']::attr(href)").getall()
        self.logger.info(f"[{response.url}] Found {len(links)} company links")

        for link in links:
            href = response.urljoin(link)
            yield CompanyLinkItem(href=href)

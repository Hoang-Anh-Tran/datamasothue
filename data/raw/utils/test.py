# import unittest
# from unittest.mock import patch, MagicMock
# from masothue.middleware import TMProxyMiddleware
# from scrapy.http import Request, Response
# from scrapy.spiders import Spider
# from scrapy.exceptions import IgnoreRequest

# class DummySpider(Spider):
#     name = "dummy"

# class TestTMProxyMiddleware(unittest.TestCase):

#     @patch("utils.tmproxy.get_current_proxy", return_value="123.123.123.123:3128")
#     @patch("utils.tmproxy.get_auth_header", return_value="Basic dGVzdF9hcGlfa2V5OmFueQ==")
#     def test_process_request_with_valid_proxy(self, mock_auth, mock_current_proxy):
#         mw = TMProxyMiddleware()
#         request = Request(url="http://example.com")
#         spider = DummySpider()

#         mw.process_request(request, spider)

#         self.assertEqual(request.meta["proxy"], "http://123.123.123.123:3128")
#         self.assertEqual(request.headers["Proxy-Authorization"], b"Basic dGVzdF9hcGlfa2V5OmFueQ==")

#     @patch("utils.tmproxy.get_current_proxy", return_value=None)
#     @patch("utils.tmproxy.get_new_proxy", return_value=None)
#     def test_process_request_without_proxy(self, mock_new_proxy, mock_current_proxy):
#         mw = TMProxyMiddleware()
#         request = Request(url="http://example.com")
#         spider = DummySpider()

#         with self.assertRaises(IgnoreRequest):
#             mw.process_request(request, spider)

#     @patch("utils.tmproxy.get_new_proxy", return_value="111.111.111.111:8080")
#     @patch("utils.tmproxy.get_auth_header", return_value="Basic dGVzdF9hcGlfa2V5OmFueQ==")
#     def test_process_response_403_and_refresh_proxy(self, mock_auth, mock_new_proxy):
#         mw = TMProxyMiddleware()
#         mw.proxy = "old.proxy:3128"
#         mw.auth_header = "Basic oldheader"
#         request = Request(url="http://example.com", dont_filter=False)
#         spider = DummySpider()
#         response = Response(url="http://example.com", status=403)

#         new_request = mw.process_response(request, response, spider)

#         self.assertTrue(new_request.dont_filter)
#         self.assertEqual(new_request.meta["proxy"], "http://111.111.111.111:8080")
#         self.assertEqual(new_request.headers["Proxy-Authorization"], b"Basic dGVzdF9hcGlfa2V5OmFueQ==")

#     @patch("utils.tmproxy.get_new_proxy", return_value=None)
#     def test_process_response_403_no_new_proxy(self, mock_new_proxy):
#         mw = TMProxyMiddleware()
#         mw.proxy = "old.proxy:3128"
#         mw.auth_header = "Basic oldheader"
#         request = Request(url="http://example.com")
#         spider = DummySpider()
#         response = Response(url="http://example.com", status=403)

#         with self.assertRaises(IgnoreRequest):
#             mw.process_response(request, response, spider)

#     def test_process_response_200_ok(self):
#         mw = TMProxyMiddleware()
#         mw.proxy = "proxy.example.com"
#         mw.auth_header = "Basic auth"
#         request = Request(url="http://example.com")
#         spider = DummySpider()
#         response = Response(url="http://example.com", status=200)

#         result = mw.process_response(request, response, spider)
#         self.assertEqual(result, response)
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Scrapy crawler để lấy page source
Chạy: python simple_scraper.py
"""

import scrapy
import sys
from scrapy.crawler import CrawlerProcess
import pandas as pd

class SimpleSpider(scrapy.Spider):
    name = 'simple'
    
    def __init__(self, url='https://quotes.toscrape.com/'):
        self.start_urls = [url]
    
    def parse(self, response):
        # Lấy page source
        page_source = response.text
        df = pd.read_html(page_source,header=None)[0]
        df.columns  = ['key', 'value']

        print(df)
        df = df.to_dict(orient="records")
        print(df)

if __name__ == '__main__':
    # Lấy URL từ command line hoặc dùng mặc định
    url = sys.argv[1] if len(sys.argv) > 1 else 'https://quotes.toscrape.com/'
    
    print(f"Crawling: {url}")
    
    # Chạy spider
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/5.0 (compatible; SimpleBot/1.0)',
        'ROBOTSTXT_OBEY': True
    })
    
    process.crawl(SimpleSpider, url=url)
    process.start()




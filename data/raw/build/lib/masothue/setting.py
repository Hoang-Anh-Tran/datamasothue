BOT_NAME = "masothue"

SPIDER_MODULES = ["masothue.spiders"]
NEWSPIDER_MODULE = "masothue.spiders"

ROBOTSTXT_OBEY = False

ITEM_PIPELINES = {
    "masothue.pipelines.PostgresPipeline": 300,
}

DOWNLOAD_DELAY = 0.5
AUTOTHROTTLE_ENABLED = False
AUTOTHROTTLE_START_DELAY = 2
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"

RETRY_ENABLED = True
RETRY_TIMES = 5
RETRY_HTTP_CODES = [429, 403, 500, 502, 503, 504]

COOKIES_ENABLED = False

# settings.py

# Bật Splash
DOWNLOADER_MIDDLEWARES = {
    "scrapy_splash.SplashCookiesMiddleware": 723,
    "scrapy_splash.SplashMiddleware": 725,
    "scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware": 810,
}

SPIDER_MIDDLEWARES = {
    "scrapy_splash.SplashDeduplicateArgsMiddleware": 100,
}

# Dùng Splash để chống duplicate URL (theo args)
DUPEFILTER_CLASS = "scrapy_splash.SplashAwareDupeFilter"
HTTPCACHE_STORAGE = "scrapy_splash.SplashAwareFSCacheStorage"

# URL của Splash server
SPLASH_URL = "http://localhost:8050"

# Tăng số lượng concurrent requests
CONCURRENT_REQUESTS = 32

# Tăng số concurrent request per domain
CONCURRENT_REQUESTS_PER_DOMAIN = 16

# Giảm thời gian delay giữa các request nếu server chịu được
DOWNLOAD_DELAY = 0.25

# Đối với Splash (vì dùng trình duyệt để render), nên hạn chế vừa đủ
SPLASH_COOKIES_DEBUG = False
SPLASH_LOG_400 = True
DUPEFILTER_CLASS = 'scrapy_splash.SplashAwareDupeFilter'
HTTPCACHE_STORAGE = 'scrapy_splash.SplashAwareFSCacheStorage'


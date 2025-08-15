BOT_NAME = "masothue"

SPIDER_MODULES = ["masothue.spiders"]
NEWSPIDER_MODULE = "masothue.spiders"

ROBOTSTXT_OBEY = False
COOKIES_ENABLED = False

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
)

# Pipelines
ITEM_PIPELINES = {
    "masothue.pipelines.PostgresPipeline": 300,
}

# Throttle và delay
DOWNLOAD_DELAY = 1.0
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 4
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0


# Retry cấu hình
RETRY_ENABLED = True
RETRY_TIMES = 5
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 403, 407]
DOWNLOAD_FAIL_ON_DATALOSS = False

# Middleware tùy chỉnh
DOWNLOADER_MIDDLEWARES = {
    "masothue.middleware.TMProxyMiddleware": 350,
    "masothue.middleware.TMProxyRetryMiddleware": 550,
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": None,
    "scrapy_splash.SplashCookiesMiddleware": 723,
    "scrapy_splash.SplashMiddleware": 725,
    "scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware": 810,
}

SPIDER_MIDDLEWARES = {
    "scrapy_splash.SplashDeduplicateArgsMiddleware": 100,
}

# # Splash cấu hình
# SPLASH_URL = "http://localhost:8050"
# SPLASH_COOKIES_DEBUG = False
# SPLASH_LOG_400 = True
# DUPEFILTER_CLASS = "scrapy_splash.SplashAwareDupeFilter"
# HTTPCACHE_STORAGE = "scrapy_splash.SplashAwareFSCacheStorage"

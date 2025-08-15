import os
import time
import base64
import logging
import requests
from dotenv import load_dotenv
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.exceptions import IgnoreRequest

load_dotenv()
logger = logging.getLogger(__name__)

TM_API_KEY = os.getenv("TM_PROXY_API_KEY")
if not TM_API_KEY:
    raise ValueError("[TMProxy] Chưa cấu hình TM_PROXY_API_KEY trong .env!")

GET_NEW_RETRY_INTERVAL = 100  

def get_new_proxy():
    """Gọi API TMProxy lấy proxy mới"""
    try:
        resp = requests.post(
            "https://tmproxy.com/api/proxy/get-new-proxy",
            json={"api_key": TM_API_KEY},
            timeout=10
        )
        data = resp.json()
        if data.get("code") == 0 and data.get("data"):
            proxy_data = data["data"]
            return {
                "proxy": proxy_data["https"],
                "username": proxy_data.get("username"),
                "password": proxy_data.get("password"),
                "expire_at": time.time() + proxy_data["timeout"] - 5
            }
        elif "retry after" in (data.get("message") or "").lower():
            logger.warning(f"[TMProxy] Chưa thể đổi proxy → retry sau")
        else:
            logger.error(f"[TMProxy] Lỗi lấy proxy mới: {data.get('message')}")
    except Exception as e:
        logger.error(f"[TMProxy] Exception gọi get_new_proxy: {e}")
    return None

def get_current_proxy():
    """Gọi API TMProxy lấy proxy hiện tại (current)"""
    try:
        resp = requests.post(
            "https://tmproxy.com/api/proxy/get-current-proxy",
            json={"api_key": TM_API_KEY},
            timeout=10
        )
        data = resp.json()
        if data.get("code") == 0 and data.get("data"):
            proxy_data = data["data"]
            return {
                "proxy": proxy_data["https"],
                "username": proxy_data.get("username"),
                "password": proxy_data.get("password"),
                "expire_at": time.time() + proxy_data.get("timeout", 30) - 5
            }
        else:
            logger.warning(f"[TMProxy] Không lấy được current proxy: {data.get('message')}")
    except Exception as e:
        logger.error(f"[TMProxy] Exception gọi get_current_proxy: {e}")
    return None

def get_proxy_auth_header(username, password):
    """Tạo Proxy-Authorization header từ user/pass."""
    auth_str = f"{username}:{password}"
    return f"Basic {base64.b64encode(auth_str.encode()).decode()}"

class TMProxyMiddleware:
    """Middleware gán proxy, fallback current nếu get_new thất bại, retry get_new sau 100s"""
    def process_request(self, request, spider):
        if not hasattr(spider, 'proxy_cache'):
            spider.proxy_cache = {
                "proxy": None,
                "username": None,
                "password": None,
                "expire_at": 0,
                "last_get_new_attempt": 0
            }

        now = time.time()
        cache = spider.proxy_cache

        
        need_get_new = False
        if not cache["proxy"] or cache["expire_at"] <= now:
           
            need_get_new = True
        elif now - cache.get("last_get_new_attempt", 0) > GET_NEW_RETRY_INTERVAL:
            
            need_get_new = True

        if need_get_new:
            cache["last_get_new_attempt"] = now
            new_proxy = get_new_proxy()
            if new_proxy:
                cache.update(new_proxy)
            else:
                
                current_proxy = get_current_proxy()
                if current_proxy:
                    cache.update(current_proxy)
                    spider.logger.info("[TMProxy] Dùng current proxy sau khi get_new thất bại")
                else:
                    spider.logger.warning("[TMProxy] Không lấy được proxy mới hoặc current")

       
        if cache["proxy"]:
            proxy_url = f"http://{cache['proxy']}"
            request.meta["proxy"] = proxy_url
            if cache["username"] and cache["password"]:
                request.headers["Proxy-Authorization"] = get_proxy_auth_header(
                    cache["username"], cache["password"]
                )
            spider.logger.debug(f"[TMProxy] Gán proxy: {proxy_url}")
        else:
            spider.logger.warning("[TMProxy] Không lấy được proxy!")

class TMProxyRetryMiddleware(RetryMiddleware):
    """Retry khi proxy chết hoặc bị chặn (HTTP 403/407 hoặc exception)."""
    def process_response(self, request, response, spider):
        if response.status in [403, 407]:
            spider.logger.warning(f"[TMProxy] Lỗi HTTP {response.status} → retry với proxy mới/current")
            return self._retry_with_new_proxy(request, spider)
        return response

    def process_exception(self, request, exception, spider):
        spider.logger.warning(f"[TMProxy] Exception: {exception} → retry với proxy mới/current")
        return self._retry_with_new_proxy(request, spider)

    def _retry_with_new_proxy(self, request, spider):
        if not hasattr(spider, 'proxy_cache'):
            spider.proxy_cache = {"proxy": None, "username": None, "password": None,
                                  "expire_at": 0, "last_get_new_attempt": 0}

        
        spider.proxy_cache["expire_at"] = 0

        now = time.time()
        spider.proxy_cache["last_get_new_attempt"] = now

        new_proxy = get_new_proxy()
        if new_proxy:
            spider.proxy_cache.update(new_proxy)
        else:
            current_proxy = get_current_proxy()
            if current_proxy:
                spider.proxy_cache.update(current_proxy)
                spider.logger.info("[TMProxy] Retry với current proxy")
            else:
                spider.logger.error("[TMProxy] Không lấy được proxy mới hoặc current → bỏ request")
                raise IgnoreRequest()

        proxy_url = f"http://{spider.proxy_cache['proxy']}"
        request.meta["proxy"] = proxy_url
        if spider.proxy_cache["username"] and spider.proxy_cache["password"]:
            request.headers["Proxy-Authorization"] = get_proxy_auth_header(
                spider.proxy_cache["username"], spider.proxy_cache["password"]
            )
        request.dont_filter = True
        time.sleep(1)
        spider.logger.info(f"[TMProxy] Retry với proxy: {proxy_url}")
        return request

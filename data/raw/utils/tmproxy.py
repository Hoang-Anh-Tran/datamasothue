import requests
import time
import logging
from config import TM_PROXY_API_KEY

logger = logging.getLogger(__name__)

proxy_cache = {
    "proxy": None,
    "expire_at": 0
}

def extract_wait_time(msg: str) -> int:
    try:
        parts = msg.lower().split("retry after")
        seconds = int(parts[1].strip().split(" ")[0])
        return seconds
    except:
        return 60

def get_current_proxy():
    try:
        res = requests.post("https://tmproxy.com/api/proxy/get-current-proxy", json={"api_key": TM_PROXY_API_KEY}, timeout=10)
        data = res.json()
        if data.get("code") == 0:
            proxy = data["data"]["https"]
            timeout = data["data"]["timeout"]
            logger.info(f"[TMProxy] Dùng lại proxy hiện tại: {proxy} (timeout: {timeout}s)")
            proxy_cache["proxy"] = proxy
            proxy_cache["expire_at"] = time.time() + timeout - 5
            return proxy
        else:
            logger.warning(f"[TMProxy] Lỗi get-current-proxy: {data.get('message')}")
    except Exception as e:
        logger.warning(f"[TMProxy] Exception khi gọi get-current-proxy: {e}")
    return None

def get_new_proxy():
    now = time.time()

    
    if proxy_cache["proxy"] and proxy_cache["expire_at"] > now:
        return proxy_cache["proxy"]

    
    proxy = get_current_proxy()
    if proxy:
        return proxy

    
    try:
        res = requests.post("https://tmproxy.com/api/proxy/get-new-proxy", json={
            "api_key": TM_PROXY_API_KEY,
            "id_location": 0,
            "id_isp": 0
        }, timeout=10)
        data = res.json()
        if data.get("code") == 0:
            proxy = data["data"]["https"]
            timeout = data["data"]["timeout"]
            proxy_cache["proxy"] = proxy
            proxy_cache["expire_at"] = now + timeout - 5
            logger.info(f"[TMProxy] Proxy mới: {proxy} (timeout: {timeout}s)")
            return proxy
        elif data.get("code") == 1 and "retry after" in data.get("message", ""):
            wait_time = extract_wait_time(data["message"])
            logger.warning(f"[TMProxy] Rate limit. Retry after {wait_time}s → fallback sang get_current_proxy")
            return get_current_proxy()
        else:
            logger.error(f"[TMProxy] Lỗi từ TMProxy: {data.get('message')}")
    except Exception as e:
        logger.error(f"[TMProxy] Exception khi gọi get-new-proxy: {e}")

    return None

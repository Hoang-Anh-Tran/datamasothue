import psycopg2
import requests
import pandas as pd
import numpy as np
import json
import io
import os
import time
import base64
from dotenv import load_dotenv
from utils.db import get_db_connection

load_dotenv()
TM_API_KEY = os.getenv("TM_PROXY_API_KEY")
GET_NEW_RETRY_INTERVAL = 100  

if not TM_API_KEY:
    raise ValueError("[!] Chưa cấu hình TMPROXY_API_KEY trong .env")


def get_new_proxy():
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
        else:
            print(f"[TMProxy] get_new_proxy fail: {data.get('message')}")
    except Exception as e:
        print(f"[TMProxy] get_new_proxy error: {e}")
    return None


def get_current_proxy():
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
            print(f"[TMProxy] get_current_proxy fail: {data.get('message')}")
    except Exception as e:
        print(f"[TMProxy] get_current_proxy error: {e}")
    return None


proxy_cache = {
    "proxy": None,
    "username": None,
    "password": None,
    "expire_at": 0,
    "last_get_new_attempt": 0
}


def get_working_proxy():
    """Lặp cho tới khi lấy được proxy khả dụng."""
    global proxy_cache
    while True:
        now = time.time()
        need_get_new = False

        if not proxy_cache["proxy"] or proxy_cache["expire_at"] <= now:
            need_get_new = True
        elif now - proxy_cache.get("last_get_new_attempt", 0) > GET_NEW_RETRY_INTERVAL:
            need_get_new = True

        if need_get_new:
            proxy_cache["last_get_new_attempt"] = now
            new_proxy = get_new_proxy()
            if new_proxy:
                proxy_cache.update(new_proxy)
                print(f"[TMProxy] Lấy proxy mới: {proxy_cache['proxy']}")
                return proxy_cache
            else:
                current_proxy = get_current_proxy()
                if current_proxy:
                    proxy_cache.update(current_proxy)
                    print(f"[TMProxy] Fallback sang current proxy: {proxy_cache['proxy']}")
                    return proxy_cache
                else:
                    print("[TMProxy] Không lấy được proxy, thử lại sau 5s...")
                    time.sleep(5)
        else:
            return proxy_cache


def upsert_data(data, tax_code):
    conn = get_db_connection()
    cur = conn.cursor()

    sql = """
        INSERT INTO company_tax_info_table (tax_code, data)
        VALUES (%s, %s)
        ON CONFLICT (tax_code) DO UPDATE SET data = EXCLUDED.data
    """
    cur.execute(sql, (tax_code, json.dumps(data, ensure_ascii=False)))
    conn.commit()
    cur.close()
    conn.close()
    print(f"[+] Đã lưu dữ liệu cho {tax_code}")


def parse_detail(html_text, tax_code):
    try:
        data = pd.read_html(io.StringIO(html_text))[0]
        data.columns = ['key', 'value']
        data = data.replace({np.nan: None})
        data = data.to_dict(orient="records")
        upsert_data(data, tax_code)
    except Exception as e:
        print(f"[!] Lỗi khi parse dữ liệu cho {tax_code}: {e}")


def fetch_with_retry(href, headers, tax_code, max_retries=10):
    """Request với retry khi gặp 403, 407, hoặc lỗi mạng."""
    attempt = 0
    while attempt < max_retries:
        attempt += 1
        proxy_info = get_working_proxy()
        # proxies = {
        #     "http": f"http://{proxy_info['proxy']}",
        #     "https": f"http://{proxy_info['proxy']}"
        # }
        proxy_url = proxy_info['proxy']
        if proxy_info.get("username") and proxy_info.get("password"):
            proxy_url = f"http://{proxy_info['username']}:{proxy_info['password']}@{proxy_info['proxy']}"

        proxies = {
            "http": proxy_url,
            "https": proxy_url
        }
        try:
            response = requests.get(href, headers=headers, proxies=proxies, timeout=20)
            if response.status_code == 200:
                return response
            elif response.status_code in [403, 407]:
                print(f"[!] HTTP {response.status_code}, đổi proxy và retry (lần {attempt})...")
                proxy_cache["expire_at"] = 0  # ép lấy proxy mới lần sau
                continue
            else:
                print(f"[!] Request thất bại, status_code={response.status_code}")
                return None
        except Exception as e:
            print(f"[!] Lỗi khi request qua proxy (lần {attempt}): {e}")
            proxy_cache["expire_at"] = 0
            continue
    print("[!] Quá số lần retry, bỏ qua.")
    return None


def main():
    tax_code = input("Nhập mã số thuế: ").strip()

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT href FROM company_tax_link_4 WHERE tax_id = %s", (tax_code,))
    row = cur.fetchone()
    conn.close()

    if not row:
        print(f"[!] Không tìm thấy {tax_code} trong DB")
        return

    href = row[0]
    print(f"[+] Tìm thấy href: {href}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
        "Referer": "https://masothue.com/",
    }

    response = fetch_with_retry(href, headers, tax_code)
    if response:
        parse_detail(response.text, tax_code)


if __name__ == "__main__":
    main()

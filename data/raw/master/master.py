# import subprocess
# import threading
# import time
# import os
# import redis
# from utils.tmproxy import get_new_proxy
# from dotenv import load_dotenv

# load_dotenv()

# REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
# REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
# REDIS_QUEUE = os.getenv("REDIS_QUEUE", "masothue_taxcode")
# NUM_WORKERS = int(os.getenv("NUM_WORKERS", 5))
# PROXY_REFRESH_INTERVAL = int(os.getenv("PROXY_REFRESH_INTERVAL", 300))

# redis_conn = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
# current_proxy = None
# proxy_lock = threading.Lock()

# def update_proxy_periodically():
#     global current_proxy
#     while True:
#         try:
#             proxy = get_new_proxy()
#             if proxy:
#                 with proxy_lock:
#                     current_proxy = proxy
#                 print(f"[MASTER]  Proxy mới: {proxy}")
#             else:
#                 print("[MASTER]  Không thể lấy proxy mới.")
#         except Exception as e:
#             print(f"[MASTER]  Lỗi khi cập nhật proxy: {e}")
#         time.sleep(PROXY_REFRESH_INTERVAL)

# # --- Spider Execution ---
# def run_spider(spider_name, extra_args=None):
#     cmd = ["scrapy", "crawl", spider_name]
#     if extra_args:
#         cmd += extra_args
#     print(f"[MASTER]  Chạy spider: {' '.join(cmd)}")
#     return subprocess.Popen(cmd)

# def run_link_spider_loop():
#     while True:
#         print("[MASTER]  Bắt đầu crawl link công ty với link_spider...")
#         try:
#             proc = run_spider("link_spider")
#             proc.wait()
#             print("[MASTER] link_spider đã kết thúc, khởi động lại sau 30 giây...")
#         except Exception as e:
#             print(f"[MASTER]  Lỗi khi chạy link_spider: {e}")
#         time.sleep(30)

# def run_worker_loop():
#     while True:
#         try:
#             if redis_conn.llen(REDIS_QUEUE) == 0:
#                 print("[MASTER]  Hàng đợi trống. Chờ thêm dữ liệu từ link_spider...")
#                 time.sleep(10)
#                 continue
#             print("[MASTER]  Worker bắt đầu xử lý dữ liệu...")
#             proc = run_spider("detail_worker_spider")
#             proc.wait()
#         except Exception as e:
#             print(f"[MASTER] Lỗi worker: {e}")
#             time.sleep(10)

# # --- Main Controller ---
# def main():
#     print("[MASTER] Đang khởi động hệ thống master...")

#     # 1. Thread đổi proxy
#     threading.Thread(target=update_proxy_periodically, daemon=True).start()

#     # 2. Thread chạy link_spider liên tục
#     threading.Thread(target=run_link_spider_loop, daemon=True).start()

#     # 3. Worker threads
#     for i in range(NUM_WORKERS):
#         threading.Thread(target=run_worker_loop, daemon=True).start()
#         time.sleep(1)  # tránh start dồn 1 lúc gây nghẽn CPU

#     print("[MASTER] Hệ thống master đã sẵn sàng.")
#     while True:
#         time.sleep(60)

# if __name__ == "__main__":
#     main()

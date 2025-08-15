Crawler lấy link công ty và chi tiết công ty từ masothue.com bằng Scrapy + Redis + PostgreSQL

1.Thư viện cần cài:
      ---Thư viện scrapyd và web điều chỉnh các spider---
--->Bật terminal và nhập lệnh:
pip install scrapy
pip install scrapy-redis
pip install scrapyd
pip install scrapyd-client
pip install scrapydweb
pip install logparser

                                  ---Thư viện redis---
--->Bật terminal và nhập lệnh:
pip install redis
sudo apt update
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server


                          ---Deploy spider lên scrapyd---
--->Bật terminal và nhập lệnh:
scrapyd-deploy default -p masothue

                                  ---Các thư viện khác---
--->Bật terminal và nhập lệnh:
pip install python-dotenv
pip install lxml
pip install requests
pip install pandas
pip install tmproxy

2.Setting .env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

3.Database
                     ---Bảng database---
Khởi tạo 2 tables:

Table 1:
create table company_tax_link_4(
	tax_id TEXT PRIMARY KEY,
	href TEXT
);

Table 2:
create table company_tax_info_table(
	tax_code VARCHAR(50) PRIMARY KEY,
	data JSONB
);


4.Các bước chạy chương trình
-->Bật 3 terminal
a.Terminal 1: Nhập lệnh "cd masothue/data/raw" sau đó nhấn enter. Tiếp đó nhập lênh "scrapyd" để khơi động scrapyd
b.Terminal 2:Nhập lệnh "cd masothue/data/raw" sau đó nhấn enter.Tiếp đó nhập lệnh "scrapydweb" để mở giao diện quản lý spider làm việc
c.Terminal 3: Nhập lệnh "cd masothue/data/raw" sau đó nhấn enter.Tiếp đó nhập lệnh "logparser" để có thể xem log hoạt động của spider trong giao diện scrapydweb
--> Khi đã bật hết tất cả thì bấm vào terminal 2 và bấm vào link ở dòng có hiện : [2025-08-14 14:20:03,926] INFO     in werkzeug:  * Running on http://172.16.42.138:5000/ (Press CTRL+C to quit) (ví dụ minh họa)
-->Ctrl + click vào link htttps đó để mở giao diện scrapydweb
--> Trong giao diện scrapydweb chọn run spider
      ->project chọn default
      ->version chọn default: the lastest version
      ->spider chọn 1 trong 2: link_spider(nếu muốn crawl link công ty) và detail_worker_spider(nếu muốn crawl thông tin chi tiết)
--> Sau đó chuyển sang phần Jobs để xem các spider nào đang chạy. Có thể bấm "stop" nếu muốn dừng spider và bấm "start" nếu muốn bắt đầu spider nào đó.Trong khi spider đang hoạt động có thể bấm "log" để xem log hoạt động của spider.
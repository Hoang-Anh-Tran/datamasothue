from selenium import webdriver
import json
from selenium.webdriver.chrome.options import Options
import time

options = Options()
options.headless = False

driver = webdriver.Chrome(options=options)
driver.get("https://masothue.com")

print("Giải CAPTCHA bằng tay rồi bấm Enter để tiếp tục...")
input()

cookies = driver.get_cookies()
with open("cookies.json", "w") as f:
    json.dump(cookies, f)

print("Cookie đã được lưu vào cookies.json")
driver.quit()

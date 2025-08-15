import redis
import os
from dotenv import load_dotenv

load_dotenv()

r = redis.Redis(host = os.getenv("REDIS_HOST"),
                port = int(os.getenv("REDIS_PORT")),
                db = 0)

while True:
    taxcode = input("Enter tax code: ")
    if taxcode:
        r.lpush(os.getenv("REDIS_QUEUE"), taxcode)
        print(f"Tax code {taxcode} added to the queue.")
import redis
import os
from dotenv import load_dotenv

load_dotenv()

def get_redis_queue():
    return redis.Redis(
        host = os.getenv("REDIS_HOST"),
        port = int(os.getenv("REDIS_PORT")),
        db = 0
    )

def pop_taxcode(queue_name):
    r = get_redis_queue()
    return r.rpop(queue_name)
import redis
import json
import os

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
redis_client = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)

def get_cache(key: str):
    data = redis_client.get(key)
    return json.loads(data) if data else None

def set_cache(key: str, value: dict):
    redis_client.set(key, json.dumps(value), ex=3600)

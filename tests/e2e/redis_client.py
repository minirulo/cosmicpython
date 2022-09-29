import redis
from allocation import config

r = redis.Redis(**config.get_redis_host_and_port())


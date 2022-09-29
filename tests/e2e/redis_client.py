import redis
from allocation import config
from allocation.domain import events


r = redis.Redis(**config.get_redis_host_and_port())

def subscribe_to(channel: str):
    pubsub = r.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe("change_batch_quantity")


def publish_to(channel: str, event: events.Event):
    pubsub = r.pubsub(ignore_subscribe_messages=True)
    pubsub.publish("change_batch_quantity") 
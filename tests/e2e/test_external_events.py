import uuid
from allocation import config
import requests
from tenacity import Retrying, stop_after_delay
import json

from . import redis_client


def random_suffix():
    return uuid.uuid4().hex[:6]


def random_sku(name=""):
    return f"sku-{name}-{random_suffix()}"


def random_batchref(name=""):
    return f"batch-{name}-{random_suffix()}"


def random_reference(name=""):
    return f"order-{name}-{random_suffix()}"


def post_to_add_batch(ref, sku, quantity, eta):
    url = config.get_api_url()
    r = requests.post(
        f"{url}/add_batch", json={"ref": ref, "sku": sku, "quantity": quantity, "eta": eta}
    )
    assert r.status_code == 201

def post_to_allocate(ref, sku, quantity):
    url = config.get_api_url()
    r = requests.post(f"{url}/allocate", json={"reference": ref, "sku": sku, "quantity": quantity})
    assert r.status_code == 201
    return r

class TestRedisEvents:
    def test_change_batch_quantity_leading_to_reallocation():
        # We create some batches, and allocations
        sku, othersku = random_sku()
        earlybatch = random_batchref(1)
        laterbatch = random_batchref(2)
        post_to_add_batch(laterbatch, sku, 10, "2011-01-02")
        post_to_add_batch(earlybatch, sku, 10, "2011-01-01")
        orderid = random_reference()
        response = post_to_allocate(orderid, sku, 10)
        assert response.json()["batchref"] == earlybatch

        subscription = redis_client.subscribe_to("line_allocated")

        # Publish an event to the external event broker to change quantity
        redis_client.publish_message(  #(3)
            "change_batch_quantity",
            {"batchref": earlier_batch, "qty": 5},
        )

        # We wait for the reallocation event to come back to our subscription
        messages = []
        for attempt in Retrying(stop=stop_after_delay(3), reraise=True):  #(4)
            with attempt:
                message = subscription.get_message(timeout=1)
                if message:
                    messages.append(message)
                    print(messages)
                data = json.loads(messages[-1]["data"])
                assert data["orderid"] == orderid
                assert data["batchref"] == laterbatch
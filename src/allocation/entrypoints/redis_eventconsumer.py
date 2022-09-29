import redis
from allocation import config
from allocation.domain import commands
from allocation.adapters import orm
from allocation.service_layer import messagebus, unit_of_work
import json
import logging


logger = logging.getLogger(__name__)

r = redis.Redis(**config.get_redis_host_and_port())
messagebus = messagebus.MessageBus()


def main():
    orm.start_mappers()
    pubsub = r.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe("change_batch_quantity","allocate")

    for m in pubsub.listen():
        logger.debug("handling %s", m)
        handler = HANDLERS[m['channel']]
        handler(m)


def handle_change_batch_quantity(m):
    data = json.loads(m["data"])
    cmd = commands.ChangeBatchQuantity(ref=data["batchref"], qty=data["qty"])  #(2)
    messagebus.handle(cmd, uow=unit_of_work.SqlAlchemyUnitOfWork())


def handle_allocate(m):
    data = json.loads(m["data"])
    cmd = commands.Allocate(ref=data["orderid"], sku=data["sku"], qty=data["qty"])
    messagebus.handle(cmd, uow=unit_of_work.SqlAlchemyUnitOfWork())


HANDLERS = {
    "change_batch_quantity": handle_change_batch_quantity,
    "allocate": handle_allocate
}


if __name__ == "__main__":
    main()
from allocation.service_layer import unit_of_work
from allocation.adapters import redis_eventpublisher
def allocations(orderid: str, uow: unit_of_work.AbstractUnitOfWork):
    # We could go To the ORM
    # with uow:
    #     results = uow.session.execute(
    #         """
    #         SELECT sku, batchref FROM allocations_view WHERE orderid = :orderid
    #         """,
    #         dict(orderid=orderid)
    #     )
    # Or take profit of redis
    batches = redis_eventpublisher.get_readmodel(orderid)
    return [
        {"batchref": b.decode(), "sku": s.decode()}
        for s, b in batches.items()
    ]
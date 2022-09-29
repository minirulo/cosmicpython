from allocation.domain import events
from allocation.adapters import email
from . import unit_of_work
from allocation.domain import model
from typing import Dict, Type, List, Callable

class InvalidSku(Exception):
    pass


class NotFound(Exception):
    pass


def add_batch(
    event: events.BatchCreated,
    uow : unit_of_work.AbstractUnitOfWork
):
    with uow:
        product = uow.products.get(event.sku)
        if not product:
            product = model.Product(event.sku, [])
            uow.products.add(product)
        product.add_batch(model.Batch(event.ref, event.sku, event.qty, event.eta))
        uow.commit()

def allocate(
    event: events.AllocationRequired,
    uow: unit_of_work.AbstractUnitOfWork,
) -> str:
    line = model.OrderLine(event.ref, event.sku, event.qty)
    with uow:
        product = uow.products.get(event.sku)
        if not product:
            raise InvalidSku(f"Invalid sku {line.sku}")
        batchref = product.allocate(line)
        uow.commit()
    return batchref

def change_batch_quantity(
    event: events.ChangeBatchQuantity,
    uow: unit_of_work.AbstractUnitOfWork,
):
    with uow:
        product = uow.products.get_by_batchref(event.ref)
        if not product:
            raise NotFound(f"Batch {event.ref} not found")
        product.change_batch_quantity(event.ref, event.qty)
        uow.commit()

def send_out_of_stock_notification(
    event: events.OutOfStock,
    uow: unit_of_work.AbstractUnitOfWork,
):
    email.send_email(f"Out of stock for sku {event.sku}")


class AbstractMessageBus:
    HANDLERS: Dict[Type[events.Event], List[Callable]]

    def handle(
        self,
        event: events.Event,
        uow: unit_of_work.AbstractUnitOfWork
    ):
        results = []
        queue = [event]
        while queue:
            event = queue.pop(0)
            for handler in self.HANDLERS[type(event)]:
                results.append(handler(event, uow=uow))
                queue.extend(uow.collect_new_events())
        return results


class MessageBus(AbstractMessageBus):
    HANDLERS = {
        events.OutOfStock: [send_out_of_stock_notification],
        events.BatchCreated: [add_batch],
        events.AllocationRequired: [allocate],
        events.ChangeBatchQuantity: [change_batch_quantity]
    }
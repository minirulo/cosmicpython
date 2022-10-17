from allocation.domain import commands, events
from allocation.adapters import email, redis_eventpublisher
from . import unit_of_work
from allocation.domain import model
from typing import Union

import logging
logger = logging.getLogger(__name__)

Message = Union[events.Event, commands.Command]


class InvalidSku(Exception):
    pass


class NotFound(Exception):
    pass


def add_batch(
    command: commands.CreateBatch,
    uow : unit_of_work.AbstractUnitOfWork
):
    with uow:
        product = uow.products.get(command.sku)
        if not product:
            product = model.Product(command.sku, [])
            uow.products.add(product)
        product.add_batch(model.Batch(command.ref, command.sku, command.qty, command.eta))
        uow.commit()


def allocate(
    command: commands.Allocate,
    uow: unit_of_work.AbstractUnitOfWork,
) -> str:
    line = model.OrderLine(command.ref, command.sku, command.qty)
    with uow:
        product = uow.products.get(command.sku)
        if not product:
            raise InvalidSku(f"Invalid sku {line.sku}")
        batchref = product.allocate(line)
        uow.commit()
    return batchref


def add_allocation_to_read_model(
    event: events.Allocated,
    uow: unit_of_work.AbstractUnitOfWork,
) -> str:
    # We could Go To the ORM 
    # with uow:
    #     uow.session.execute(
    #         """
    #         INSERT INTO allocations_view (orderid, sku, batchref)
    #         VALUES (:orderid, :sku, :batchref)
    #         """,
    #         dict(orderid=event.orderid, sku=event.sku, batchref=event.batchref)
    #     )
    #     uow.commit()
    # But better take profit of redis!
    redis_eventpublisher.update_readmodel(event.orderid, event.sku, event.batchref)


def change_batch_quantity(
    command: commands.ChangeBatchQuantity,
    uow: unit_of_work.AbstractUnitOfWork,
):
    with uow:
        product = uow.products.get_by_batchref(command.ref)
        if not product:
            raise NotFound(f"Batch {command.ref} not found")
        product.change_batch_quantity(command.ref, command.qty)
        uow.commit()


def send_out_of_stock_notification(
    event: events.OutOfStock,
    uow: unit_of_work.AbstractUnitOfWork,
):
    email.send_email(f"Out of stock for sku {event.sku}")


def send_allocated_notification(
    event: events.OutOfStock,
    uow: unit_of_work.AbstractUnitOfWork,
):
    redis_eventpublisher.publish("line_allocated", event)
    

EVENT_HANDLERS = {
        events.OutOfStock: [send_out_of_stock_notification],
        events.Allocated: [
            send_allocated_notification,
            add_allocation_to_read_model,
        ]
    }

COMMAND_HANDLERS = {
    commands.CreateBatch: add_batch,
    commands.Allocate: allocate,
    commands.ChangeBatchQuantity: change_batch_quantity
}
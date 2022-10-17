from allocation.domain import commands, events
from allocation.adapters import email, redis_eventpublisher
from . import unit_of_work
from allocation.domain import model
from typing import Dict, Type, List, Callable, Union
from tenacity import Retrying, RetryError, stop_after_attempt, wait_exponential

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


class AbstractMessageBus:
    EVENT_HANDLERS: Dict[Type[events.Event], List[Callable]]
    COMMAND_HANDLERS: Dict[Type[events.Event], List[Callable]]

    def handle(
        self,
        message: Message,
        uow: unit_of_work.AbstractUnitOfWork
    ):
        results = []
        queue = [message]
        while queue:
            message = queue.pop(0)
            if isinstance(message, events.Event):
                self.handle_event(message, uow, queue)
            elif isinstance(message, commands.Command):
                result = self.handle_command(message, uow, queue)
                results.append(result)
            else:
                raise Exception(f"{message} is neither a Command nor an Event")
        return results
    
    def handle_command(
        self,
        command: commands.Command,
        uow: unit_of_work.AbstractUnitOfWork,
        queue: List[Message]
    ):
        logger.debug("handling command %s", command)
        try:
            handler = self.COMMAND_HANDLERS[type(command)]
            result = handler(command, uow=uow)
            queue.extend(uow.collect_new_events())
            return result
        except Exception as e:
            logger.exception("Erro handling command %s", command)
            raise

    def handle_event(
        self,
        event: events.Event,
        uow: unit_of_work.AbstractUnitOfWork,
        queue: List[Message]
    ):
        for handler in self.EVENT_HANDLERS[type(event)]:
            try:
                for attempt in Retrying(
                    stop=stop_after_attempt(3),
                    wait=wait_exponential()
                ):
                    with attempt:
                        logger.debug("handling event %s with handler %s", event, handler)
                        handler(event, uow=uow)
                        queue.extend(uow.collect_new_events())
            except RetryError as retry_fail:
                logger.error(
                    "Failed to handle event %s times, giving up!",
                    retry_fail.last_attempt.attempt_number
                )
                continue
    

class MessageBus(AbstractMessageBus):
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
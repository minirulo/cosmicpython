from __future__ import annotations
from typing import Optional
from datetime import date

from allocation.domain import model
from allocation.domain.model import OrderLine
from allocation.service_layer import unit_of_work


class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def add_batch(
    ref: str,
    sku: str,
    quantity: int,
    eta: Optional[date],
    uow : unit_of_work.AbstractUnitOfWork
):
    # and this could be with start_uow() as uow:
    with uow:
        uow.batches.add(model.Batch(ref, sku, quantity, eta))
        uow.commit()


def allocate(
    reference: str,
    sku: str,
    quantity: int,
    uow: unit_of_work.AbstractUnitOfWork,
) -> str:
    line = OrderLine(reference, sku, quantity)
    with uow:
        batches = uow.batches.list()
        if not is_valid_sku(line.sku, batches):
            raise InvalidSku(f"Invalid sku {line.sku}")
        batchref = model.allocate(line, batches)
        uow.commit()
    return batchref


def reallocate(
    line: OrderLine,
    uow: unit_of_work.AbstractUnitOfWork,
) -> str:
    with uow:
        batch: model.Batch = uow.batches.get(sku=line.sku)
        if batch is None:
            raise InvalidSku(f'Invalid sku {line.sku}')
        batch.deallocate(line)
        allocate(line)
        uow.commit()
    

def change_batch_quantity(
    batchref: str, new_qty: int,
    uow: AbstractUnitOfWork,
):
    with uow:
        batch = uow.batches.get(reference=batchref)
        batch.change_purchased_quantity(new_qty)
        while batch.available_quantity < 0:
            line = batch.deallocate_one()  #(1)
        uow.commit()
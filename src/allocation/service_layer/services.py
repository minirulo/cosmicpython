
#! All this services are now handled by the messagebus
from typing import Optional
from datetime import date

from allocation.domain import model
from allocation.domain.model import OrderLine
from allocation.service_layer import unit_of_work


class InvalidSku(Exception):
    pass


def add_batch(
    ref: str,
    sku: str,
    quantity: int,
    eta: Optional[date],
    uow : unit_of_work.AbstractUnitOfWork
):
    with uow:
        product = uow.products.get(sku)
        if not product:
            product = model.Product(sku, [])
            uow.products.add(product)
        product.add_batch(model.Batch(ref, sku, quantity, eta))
        uow.commit()


def allocate(
    reference: str,
    sku: str,
    quantity: int,
    uow: unit_of_work.AbstractUnitOfWork,
) -> str:
    line = OrderLine(reference, sku, quantity)
    with uow:
        product = uow.products.get(sku)
        if not product:
            raise InvalidSku(f"Invalid sku {line.sku}")
        batchref = product.allocate(line)
        uow.commit()
    return batchref


#!TODO: Adapt to Product aggregate
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
    uow: unit_of_work.AbstractUnitOfWork,
):
    with uow:
        batch = uow.batches.get(reference=batchref)
        batch.change_purchased_quantity(new_qty)
        while batch.available_quantity < 0:
            line = batch.deallocate_one()  #(1)
        uow.commit()
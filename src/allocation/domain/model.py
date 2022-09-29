from dataclasses import dataclass
from datetime import date
from typing import Set, Optional, List

from . import events, commands

class OutOfStock(Exception):
    pass


@dataclass(unsafe_hash=True)
class OrderLine:
    reference: str
    sku: str
    quantity: int


class Batch:
    def __init__(self, reference: str, sku: str, quantity: int, eta: Optional[date] = None) -> None:
        self.reference = reference
        self.sku = sku
        self.quantity = quantity
        self.allocated_orders: Set[OrderLine] = set()
        self.eta = eta

    def allocate(self, order: OrderLine) -> None:
        if self.can_allocate(order):
            self.allocated_orders.add(order)

    @property
    def allocated_quantity(self) -> int:
        return sum(line.quantity for line in self.allocated_orders)
    
    @property
    def available_quantity(self) -> int:
        return self.quantity - self.allocated_quantity
        
    def deallocate(self, order: OrderLine) -> None:
        if order in self.allocated_orders:
            self.allocated_orders.remove(order)

    def can_allocate(self, order: OrderLine) -> bool:
        if self.sku != order.sku or self.available_quantity < order.quantity:
            return False
        return True

    def deallocate_one(self) -> OrderLine:
        return self.allocated_orders.pop()

    def __eq__(self, other):
        if not isinstance(other, Batch):
            return False
        return other.reference == self.reference
    
    def __hash__(self):
        return hash(self.reference)
    
    def __gt__(self, other):
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta

class Product:
    def __init__(self, sku: str, batches: List[Batch] = [], version_number: int = 0) -> None:
        self.sku = sku
        self.batches = batches
        self.version_number = version_number
        self.events = [] # type: Union[events.Event, commands.Command]
        
    def add_batch(self, batch: Batch) -> str:
        self.batches.append(batch)

    def allocate(self, line: OrderLine) -> str:
        try:
            batch = next(b for b in sorted(self.batches) if b.can_allocate(line))
            batch.allocate(line)
            self.events.append(
                events.Allocated(line.reference, line.sku, line.quantity, batch.reference)
            )
            self.version_number += 1
            return batch.reference
        except StopIteration:
            # raise OutOfStock(f"Out of stock for sku {line.sku}")
            self.events.append(events.OutOfStock(self.sku))

    def change_batch_quantity(self, ref: str, qty: int) -> str:
            batch = next(b for b in self.batches if b.reference == ref)
            batch.quantity = qty
            self.version_number += 1
            while batch.available_quantity < 0:
                line = batch.deallocate_one()
                self.events.append(
                    commands.Allocate(line.reference, line.sku, line.quantity)
                )


#! Without aggregations
# def allocate(line: OrderLine, batches: List[Batch]) -> str:
#     try:
#         batch = next(b for b in sorted(batches) if b.can_allocate(line))
#         batch.allocate(line)
#         return batch.reference
#     except StopIteration:
#         raise OutOfStock(f"Out of stock for sku {line.sku}")

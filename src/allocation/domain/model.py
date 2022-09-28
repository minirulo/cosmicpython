from dataclasses import dataclass
from datetime import date
from typing import Set, Optional, List

from . import events

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
    def __init__(self, sku: str, batches: List[Batch] = [], product_version: int = 0) -> None:
        self.sku = sku
        self.batches = batches
        self.product_version = product_version
        self.events = []
        
    def add_batch(self, batch: Batch) -> str:
        self.batches.append(batch)

    def allocate(self, line: OrderLine) -> str:
        try:
            batch = next(b for b in sorted(self.batches) if b.can_allocate(line))
            batch.allocate(line)
            return batch.reference
        except StopIteration:
            # raise OutOfStock(f"Out of stock for sku {line.sku}")
            self.events.append(events.OutOfStock(self.sku))


#! Without aggregations
# def allocate(line: OrderLine, batches: List[Batch]) -> str:
#     try:
#         batch = next(b for b in sorted(batches) if b.can_allocate(line))
#         batch.allocate(line)
#         return batch.reference
#     except StopIteration:
#         raise OutOfStock(f"Out of stock for sku {line.sku}")

from dataclasses import dataclass
from datetime import date
from typing import Set, Optional, List


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
        if self.sku == order.sku:
            if self.available_quantity < order.quantity:
                raise OutOfStock()
            return True
        return False

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

def allocate(order: OrderLine, batches: List[Batch]):
    batch = next(b for b in sorted(batches) if b.can_allocate(order))
    batch.allocate(order)
    return batch.reference
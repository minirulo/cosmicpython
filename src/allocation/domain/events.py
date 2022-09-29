from dataclasses import dataclass
from datetime import datetime
from typing import Optional

class Event:
    pass


@dataclass
class OutOfStock(Event):
    sku: str


@dataclass
class BatchCreated(Event):
    ref: str
    sku: str
    qty: int
    eta: Optional[datetime] = None


@dataclass
class AllocationRequired(Event):
    ref: str
    sku: str
    qty: int


@dataclass
class ChangeBatchQuantity(Event):
    ref: str
    qty: int
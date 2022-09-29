from dataclasses import dataclass


class Event:
    pass


@dataclass
class OutOfStock(Event):
    sku: str


#! These are Commands now
# @dataclass
# class BatchCreated(Event):
#     ref: str
#     sku: str
#     qty: int
#     eta: Optional[datetime] = None


# @dataclass
# class AllocationRequired(Event):
#     ref: str
#     sku: str
#     qty: int


# @dataclass
# class ChangeBatchQuantity(Event):
#     ref: str
#     qty: int
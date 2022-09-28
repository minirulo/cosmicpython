from datetime import date, timedelta
import pytest

from allocation.domain.model import OrderLine, Batch, OutOfStock

today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)

def make_batch_and_line(sku, batch_quantity, line_quantity):
    return (
        Batch("Batch-001", sku, batch_quantity, eta=date.today()),
        OrderLine("order-123", sku, line_quantity),
    )


def test_allocating_to_a_batch_reduces_the_available_quantity():
    batch, order = make_batch_and_line("CHAIR", 10, 1)
    assert batch.can_allocate(order)


def test_can_allocate_if_available_greater_than_required():
    batch, order = make_batch_and_line("CHAIR", 10, 2)
    assert batch.can_allocate(order)


def test_can_allocate_if_available_equal_to_required():
    batch, order = make_batch_and_line("CHAIR", 10, 10)
    assert batch.can_allocate(order)


def test_cannot_allocate_wrong_sku():
    order = OrderLine("Order-1", "CHAIR", 20)
    batch = Batch("Batch-001", "LAMP", 10)
    assert batch.can_allocate(order) is False


def test_duplicateallocated_orders_processed_once():
    batch, order = make_batch_and_line("CHAIR", 10, 2)
    batch.allocate(order)
    batch.allocate(order)
    assert batch.available_quantity == 8


def test_can_only_deallocate_allocated_lines():
    batch, unallocated_line = make_batch_and_line("DECORATIVE-TRINKET", 20, 2)
    batch.deallocate(unallocated_line)
    assert batch.available_quantity == 20

# Moved to Service Layer
# def test_prefers_current_stock_batches_to_shipments():
#     in_stock_batch = Batch("in-stock-batch", "RETRO-CLOCK", 100, eta=None)
#     shipment_batch = Batch("shipment-batch", "RETRO-CLOCK", 100, eta=tomorrow)
#     line = OrderLine("oref", "RETRO-CLOCK", 10)

#     allocate(line, [in_stock_batch, shipment_batch])

#     assert in_stock_batch.available_quantity == 90
#     assert shipment_batch.available_quantity == 100


# Moved to Service Layer
# def test_prefers_earlier_batches():
#     earliest = Batch("speedy-batch", "MINIMALIST-SPOON", 100, eta=today)
#     medium = Batch("normal-batch", "MINIMALIST-SPOON", 100, eta=tomorrow)
#     latest = Batch("slow-batch", "MINIMALIST-SPOON", 100, eta=later)
#     line = OrderLine("order1", "MINIMALIST-SPOON", 10)

#     allocate(line, [medium, earliest, latest])

#     assert earliest.available_quantity == 90
#     assert medium.available_quantity == 100
#     assert latest.available_quantity == 100

# Moved to Service Layer
# def test_returns_allocated_batch_ref():
#     in_stock_batch = Batch("in-stock-batch-ref", "HIGHBROW-POSTER", 100, eta=None)
#     shipment_batch = Batch("shipment-batch-ref", "HIGHBROW-POSTER", 100, eta=tomorrow)
#     line = OrderLine("oref", "HIGHBROW-POSTER", 10)
#     product
#     allocation = allocate(line, [in_stock_batch, shipment_batch])
#     assert allocation == in_stock_batch.reference

# Moved to Service Layer
# def test_raises_out_of_stock_exception_if_cannot_allocate():
#     batch = Batch("batch1", "SMALL-FORK", 10, eta=today)
#     allocate(OrderLine("order1", "SMALL-FORK", 10), [batch])

#     with pytest.raises(OutOfStock):
#         allocate(OrderLine("order2", "SMALL-FORK", 1), [batch])
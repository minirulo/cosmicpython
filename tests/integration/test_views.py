from datetime import datetime
from allocation.service_layer import unit_of_work, messagebus
from allocation.domain import commands
from allocation import views


today = datetime.today()

def test_allocations_view(session_factory):
    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    bus = messagebus.MessageBus()
    bus.handle(commands.CreateBatch("sku1batch", "sku1", 50, None), uow)
    bus.handle(commands.CreateBatch("sku2batch", "sku2", 50, today), uow)
    bus.handle(commands.Allocate("order1", "sku1", 20), uow)
    bus.handle(commands.Allocate("order1", "sku2", 20), uow)
    # add a spurious batch and order to make sure we're getting the right ones
    bus.handle(commands.CreateBatch("sku1batch-later", "sku1", 50, today), uow)
    bus.handle(commands.Allocate("otherorder", "sku1", 30), uow)
    bus.handle(commands.Allocate("otherorder", "sku2", 10), uow)

    assert views.allocations("order1", uow) == [
        {"sku": "sku1", "batchref": "sku1batch"},
        {"sku": "sku2", "batchref": "sku2batch"},
    ]
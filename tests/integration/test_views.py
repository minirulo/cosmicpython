from datetime import datetime
from allocation.service_layer import unit_of_work, messagebus
from allocation.domain import commands
from allocation import views, bootstrap
from sqlalchemy.orm import clear_mappers
import pytest

today = datetime.today()
    
@pytest.fixture
def sqlite_bus(session_factory):
    bus = bootstrap.bootstrap(
        start_orm=False,
        uow=unit_of_work.SqlAlchemyUnitOfWork(session_factory),
        send_mail=lambda *args: None,
        publish=lambda *args: None,
    )
    yield bus
    clear_mappers()
    
def test_allocations_view(sqlite_bus: messagebus.MessageBus):
    sqlite_bus.handle(commands.CreateBatch("sku1batch", "sku1", 50, None))
    sqlite_bus.handle(commands.CreateBatch("sku2batch", "sku2", 50, today))
    sqlite_bus.handle(commands.Allocate("order1", "sku1", 20))
    sqlite_bus.handle(commands.Allocate("order1", "sku2", 20))
    # add a spurious batch and order to make sure we're getting the right ones
    sqlite_bus.handle(commands.CreateBatch("sku1batch-later", "sku1", 50, today))
    sqlite_bus.handle(commands.Allocate("otherorder", "sku1", 30))
    sqlite_bus.handle(commands.Allocate("otherorder", "sku2", 10))

    assert views.allocations("order1") == [
        {"sku": "sku1", "batchref": "sku1batch"},
        {"sku": "sku2", "batchref": "sku2batch"},
    ]
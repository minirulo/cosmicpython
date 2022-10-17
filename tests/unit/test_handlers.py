from allocation.adapters import repository
from allocation.service_layer import messagebus, unit_of_work
from allocation.domain import events, commands
from allocation import bootstrap
from datetime import date
from sqlalchemy.orm import clear_mappers
import pytest

class FakeRepository(repository.AbstractRepository):
    def __init__(self, products):
        super().__init__()
        self._products = set(products)

    def _add(self, product):
        self._products.add(product)

    def _get(self, sku):
        return next((b for b in self._products if b.sku == sku), None)

    def _get_by_batchref(self, ref: str):
        return next(
            (p for p in self._products for b in p.batches if b.reference == ref),
            None
        )

    def list(self):
        return list(self._products)


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self) -> None:
        self.products = FakeRepository([])
        self.committed = False

    def _commit(self):
        self.committed =True
        
    def rollback(self):
        pass


@pytest.fixture
def sqlite_bus():
    bus = bootstrap.bootstrap(
        start_orm=False,
        uow=FakeUnitOfWork(),
        send_mail=lambda *args: None,
        publish=lambda *args: None,
    )
    yield bus
    clear_mappers()


class TestAddBatch:
    def test_for_new_products(self, sqlite_bus):
        sqlite_bus.handle(commands.CreateBatch(ref="b1", sku="CRUNCHY-ARMCHAIR", qty=100, eta=None))
        assert sqlite_bus.uow.products.get("CRUNCHY-ARMCHAIR") is not None
        assert sqlite_bus.uow.committed


class TestAllocate:
    def test_allocate_returns_allocation(self, sqlite_bus):
        sqlite_bus.handle(commands.CreateBatch(ref="b1", sku="CRUNCHY-ARMCHAIR", qty=100, eta=None))
        # We will resolve this result dependency later on....
        result = sqlite_bus.handle(commands.Allocate(ref="o1",sku="CRUNCHY-ARMCHAIR",qty=10))
        assert result == ["b1"]

    
class TestChangeBatchQuantity:
    def test_available_quantity_change(self, sqlite_bus):
        sqlite_bus.handle(commands.CreateBatch(ref="b1", sku="CRUNCHY-ARMCHAIR", qty=100, eta=None))
        sqlite_bus.handle(commands.ChangeBatchQuantity(ref="b1", qty=50))
        [batch] = sqlite_bus.uow.products.get("CRUNCHY-ARMCHAIR").batches
        assert batch.available_quantity == 50

    def test_reallocate_on_quantity_change(self, sqlite_bus):
        setup = [
            commands.CreateBatch(ref="b1", sku="CRUNCHY-ARMCHAIR", qty=50, eta=None),
            commands.CreateBatch(ref="b2", sku="CRUNCHY-ARMCHAIR", qty=50, eta=date.today()),
            commands.Allocate(ref="o1",sku="CRUNCHY-ARMCHAIR",qty=10),
            commands.Allocate(ref="o2",sku="CRUNCHY-ARMCHAIR",qty=10)
        ]

        for event in setup:
            sqlite_bus.handle(event)
        
        [batch1, batch2] = sqlite_bus.uow.products.get("CRUNCHY-ARMCHAIR").batches
        assert batch1.available_quantity == 30
        assert batch2.available_quantity == 50

        sqlite_bus.handle(commands.ChangeBatchQuantity(ref="b1", qty=10))
        [batch1, batch2] = sqlite_bus.uow.products.get("CRUNCHY-ARMCHAIR").batches
        assert batch1.available_quantity == 0
        assert batch2.available_quantity == 40

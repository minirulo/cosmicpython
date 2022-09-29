from allocation.adapters import repository
from allocation.service_layer import messagebus, unit_of_work
from allocation.domain import events
from datetime import date


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


class TestAddBatch:
    def test_for_new_products(self):
        uow = FakeUnitOfWork()
        bus = messagebus.MessageBus()
        bus.handle(events.BatchCreated(ref="b1", sku="CRUNCHY-ARMCHAIR", qty=100, eta=None), uow)
        assert uow.products.get("CRUNCHY-ARMCHAIR") is not None
        assert uow.committed


class TestAllocate:
    def test_allocate_returns_allocation(self):
        uow = FakeUnitOfWork()
        bus = messagebus.MessageBus()
        bus.handle(events.BatchCreated(ref="b1", sku="CRUNCHY-ARMCHAIR", qty=100, eta=None), uow)
        # We will resolve this result dependency later on....
        result = bus.handle(events.AllocationRequired(ref="o1",sku="CRUNCHY-ARMCHAIR",qty=10), uow)
        assert result == ["b1"]

    
class TestChangeBatchQuantity:
    def test_available_quantity_change(self):
        uow = FakeUnitOfWork()
        bus = messagebus.MessageBus()
        bus.handle(events.BatchCreated(ref="b1", sku="CRUNCHY-ARMCHAIR", qty=100, eta=None), uow)
        bus.handle(events.ChangeBatchQuantity(ref="b1", qty=50), uow)
        [batch] = uow.products.get("CRUNCHY-ARMCHAIR").batches
        assert batch.available_quantity == 50

    def test_reallocate_on_quantity_change(self):
        uow = FakeUnitOfWork()
        bus = messagebus.MessageBus()
        setup = [
            events.BatchCreated(ref="b1", sku="CRUNCHY-ARMCHAIR", qty=50, eta=None),
            events.BatchCreated(ref="b2", sku="CRUNCHY-ARMCHAIR", qty=50, eta=date.today()),
            events.AllocationRequired(ref="o1",sku="CRUNCHY-ARMCHAIR",qty=10),
            events.AllocationRequired(ref="o2",sku="CRUNCHY-ARMCHAIR",qty=10)
        ]

        for event in setup:
            bus.handle(event, uow)
        
        [batch1, batch2] = uow.products.get("CRUNCHY-ARMCHAIR").batches
        assert batch1.available_quantity == 30
        assert batch2.available_quantity == 50

        bus.handle(events.ChangeBatchQuantity(ref="b1", qty=10), uow)
        [batch1, batch2] = uow.products.get("CRUNCHY-ARMCHAIR").batches
        assert batch1.available_quantity == 0
        assert batch2.available_quantity == 40

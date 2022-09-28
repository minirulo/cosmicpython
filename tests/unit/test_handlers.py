from allocation.adapters import repository
from allocation.service_layer import messagebus, unit_of_work
from allocation.domain import events

class FakeRepository(repository.AbstractRepository):
    def __init__(self, products):
        super().__init__()
        self._products = set(products)

    def _add(self, product):
        self._products.add(product)

    def _get(self, sku):
        return next((b for b in self._products if b.sku == sku), None)

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
        messagebus.handle(events.BatchCreated(ref="b1", sku="CRUNCHY-ARMCHAIR", qty=100, eta=None), uow)
        assert uow.products.get("CRUNCHY-ARMCHAIR") is not None
        assert uow.committed


class TestAllocate:
    def test_allocate_returns_allocation(self):
        uow = FakeUnitOfWork()
        messagebus.handle(events.BatchCreated(ref="b1", sku="CRUNCHY-ARMCHAIR", qty=100, eta=None), uow)
        # We will resolve this result dependency later on....
        result = messagebus.handle(events.AllocationRequired(ref="o1",sku="CRUNCHY-ARMCHAIR",qty=10), uow)
        assert result == ["b1"]
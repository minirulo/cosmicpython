import pytest
import domain.model as model
import adapters.repository as repository
import service_layer.services as services
from datetime import date, timedelta


today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)


class FakeRepository(repository.AbstractRepository):
    def __init__(self, batches):
        self._batches = set(batches)

    def add(self, batch):
        self._batches.add(batch)

    def get(self, reference):
        return next(b for b in self._batches if b.reference == reference)

    def list(self):
        return list(self._batches)


class FakeSession:
    committed = False

    def commit(self):
        self.committed = True


def test_returns_allocation():
    line = model.OrderLine("o1", "COMPLICATED-LAMP", 10)
    batch = model.Batch("b1", "COMPLICATED-LAMP", 100, eta=None)
    repo = FakeRepository([batch])

    result = services.allocate(line, repo, FakeSession())
    assert result == "b1"


def test_error_for_invalid_sku():
    line = model.OrderLine("o1", "NONEXISTENTSKU", 10)
    batch = model.Batch("b1", "AREALSKU", 100, eta=None)
    repo = FakeRepository([batch])

    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        services.allocate(line, repo, FakeSession())


def test_commits():
    line = model.OrderLine("o1", "OMINOUS-MIRROR", 10)
    batch = model.Batch("b1", "OMINOUS-MIRROR", 100, eta=None)
    repo = FakeRepository([batch])
    session = FakeSession()

    services.allocate(line, repo, session)
    assert session.committed is True


# Moved from domain
def test_prefers_current_stock_batches_to_shipments():
    in_stock_batch = model.Batch("in-stock-batch", "RETRO-CLOCK", 100, eta=None)
    shipment_batch = model.Batch("shipment-batch", "RETRO-CLOCK", 100, eta=tomorrow)
    line = model.OrderLine("oref", "RETRO-CLOCK", 10)
    repo = FakeRepository([in_stock_batch, shipment_batch])
    session = FakeSession()

    services.allocate(line, repo, session)

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100


# Moved from domain
def test_prefers_earlier_batches():
    earliest = model.Batch("speedy-batch", "MINIMALIST-SPOON", 100, eta=today)
    medium = model.Batch("normal-batch", "MINIMALIST-SPOON", 100, eta=tomorrow)
    latest = model.Batch("slow-batch", "MINIMALIST-SPOON", 100, eta=later)
    line = model.OrderLine("order1", "MINIMALIST-SPOON", 10)
    repo = FakeRepository([earliest, medium, latest])
    session = FakeSession()

    services.allocate(line, repo, session)

    assert earliest.available_quantity == 90
    assert medium.available_quantity == 100
    assert latest.available_quantity == 100


def test_deallocate_decrements_available_quantity():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "BLUE-PLINTH", 100, None, repo, session)
    line = model.OrderLine("o1", "BLUE-PLINTH", 10)
    services.allocate(line, repo, session)
    batch: model.Batch = repo.get(reference="b1")
    assert batch.available_quantity == 90
    services.deallocate(line, "b1", repo, session)
    assert batch.available_quantity == 100


@pytest.mark.skip("todo")
def test_deallocate_decrements_correct_quantity():
    ...  #  TODO - check that we decrement the right sku


@pytest.mark.skip("todo")
def test_trying_to_deallocate_unallocated_batch():
    ...  #  TODO: should this error or pass silently? up to you.

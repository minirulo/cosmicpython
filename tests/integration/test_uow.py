import pytest
from allocation.domain import model
from allocation.service_layer import unit_of_work


def insert_batch(session, ref, sku, quantity, eta):
    session.execute(
        "INSERT INTO batches (reference, sku, quantity, eta)"
        " VALUES (:ref, :sku, :quantity, :eta)",
        dict(ref=ref, sku=sku, quantity=quantity, eta=eta),
    )


def get_allocated_batch_ref(session, reference, sku):
    [[orderlineid]] = session.execute(
        "SELECT id FROM order_lines WHERE reference=:reference AND sku=:sku",
        dict(reference=reference, sku=sku),
    )
    [[batchref]] = session.execute(
        "SELECT b.reference FROM allocations JOIN batches AS b ON batch_id = b.id"
        " WHERE order_id=:orderlineid",
        dict(orderlineid=orderlineid),
    )
    return batchref


def test_uow_can_retrieve_a_batch_and_allocate_to_it(session_factory):
    session = session_factory()
    insert_batch(session, "batch1", "HIPSTER-WORKBENCH", 100, None)
    session.commit()

    # pytest.fail("decide what your UoW looks like first?")
    # either:
    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with uow:

    # or perhaps
    # with unit_of_work.start(session_factory) as uow: ?

        batch = uow.batches.get(reference='batch1')
        line = model.OrderLine('o1', 'HIPSTER-WORKBENCH', 10)
        batch.allocate(line)
        uow.commit()

    batchref = get_allocated_batch_ref(session, "o1", "HIPSTER-WORKBENCH")
    assert batchref == "batch1"


def test_rolls_back_uncommitted_work_by_default(session_factory):
    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with uow:
        insert_batch(uow.session, "batch1", "MEDIUM-PLINTH", 100, None)

    new_session = session_factory()
    rows = list(new_session.execute('SELECT * FROM "batches"'))
    assert rows == []


def test_rolls_back_on_error(session_factory):
    class MyException(Exception):
        pass

    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with pytest.raises(MyException):
        with uow:
            insert_batch(uow.session, "batch1", "LARGE-FORK", 100, None)
            raise MyException()

    new_session = session_factory()
    rows = list(new_session.execute('SELECT * FROM "batches"'))
    assert rows == []

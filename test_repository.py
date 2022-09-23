import model
import repository


def insert_order_line(session):
    session.execute(
        "INSERT INTO order_lines (orderid, sku, quantity)"
        ' VALUES ("order1", "GENERIC-SOFA", 12)'
    )
    [[orderline_id]] = session.execute(
        "SELECT id FROM order_lines WHERE orderid=:orderid AND sku=:sku",
        dict(orderid="order1", sku="GENERIC-SOFA"),
    )
    return orderline_id


def test_repository_can_save_a_batch(session):    
    batch = model.Batch("Batch-001", "LAMP", 10)
    repository = repository.SqlAlchemyRepository(session)
    repository.add(batch)
    repository.commit()

    rows = session.execute(
        'SELECT reference, sku, _purchased_quantity, eta FROM "batches"'
    )
    assert list(rows) == [("Batch-001", "LAMP", 10, None)]


def test_repository_can_retrieve_a_batch_with_allocations(session):
    orderline_id = insert_order_line(session)
    batch1_id = insert_batch(session, "Batch-001")
    insert_batch(session, "Batch-002")
    insert_allocation(session, orderline_id, batch1_id)  #(2)

    repo = repository.SqlAlchemyRepository(session)
    retrieved = repo.get("Batch-001")

    expected = model.Batch("Batch-001", "LAMP", 10, eta=None)
    assert retrieved == expected
    assert retrieved.sku == expected.sku
    assert retrieved.quantity == expected.quantity
    assert retrieved.allocated_orders == {
        model.OrderLine("order1", "GENERIC-SOFA", 12),
    }
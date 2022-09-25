import model
import repository


def insert_order_line(session):
    session.execute(
        "INSERT INTO order_lines (reference, sku, quantity)"
        ' VALUES ("order1", "GENERIC-SOFA", 12)'
    )
    [[order_id]] = session.execute(
        "SELECT id FROM order_lines WHERE reference=:reference AND sku=:sku",
        dict(reference="order1", sku="GENERIC-SOFA"),
    )
    return order_id

def insert_batch(session, batch_id):
    session.execute(
        "INSERT INTO batches (reference, sku, quantity, eta)"
        ' VALUES (:batch_id, "GENERIC-SOFA", 100, null)',
        dict(batch_id=batch_id),
    )
    [[batch_id]] = session.execute(
        'SELECT id FROM batches WHERE reference=:batch_id AND sku="GENERIC-SOFA"',
        dict(batch_id=batch_id),
    )
    return batch_id


def insert_allocation(session, order_id, batch_id):
    session.execute(
        "INSERT INTO allocations (order_id, batch_id)"
        " VALUES (:order_id, :batch_id)",
        dict(order_id=order_id, batch_id=batch_id),
    )

    
def test_repository_can_save_a_batch(session):    
    batch = model.Batch("Batch-001", "LAMP", 10)
    repo = repository.SqlAlchemyRepository(session)
    repo.add(batch)
    repo.commit()

    rows = session.execute(
        'SELECT reference, sku, quantity, eta FROM "batches"'
    )
    assert list(rows) == [("Batch-001", "LAMP", 10, None)]


def test_repository_can_retrieve_a_batch_withallocated_orders(session):
    order_id = insert_order_line(session)
    batch1_id = insert_batch(session, "Batch-001")
    insert_batch(session, "Batch-002")
    insert_allocation(session, order_id, batch1_id)  #(2)

    repo = repository.SqlAlchemyRepository(session)
    retrieved = repo.get("Batch-001")

    expected = model.Batch("Batch-001", "GENERIC-SOFA", 100, eta=None)
    assert retrieved == expected
    assert retrieved.sku == expected.sku
    assert retrieved.quantity == expected.quantity
    assert retrieved.allocated_orders == {
        model.OrderLine("order1", "GENERIC-SOFA", 12)
    }

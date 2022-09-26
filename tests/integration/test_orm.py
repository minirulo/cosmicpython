import allocation.domain.model as model

from datetime import date


def test_orderline_mapper_can_load_lines(session):
    session.execute(
        "INSERT INTO order_lines (reference, sku, quantity) VALUES "
        '("order1", "RED-CHAIR", 12),'
        '("order1", "RED-TABLE", 13),'
        '("order2", "BLUE-LIPSTICK", 14)'
    )
    expected = [
        model.OrderLine("order1", "RED-CHAIR", 12),
        model.OrderLine("order1", "RED-TABLE", 13),
        model.OrderLine("order2", "BLUE-LIPSTICK", 14),
    ]
    assert session.query(model.OrderLine).all() == expected


def test_orderline_mapper_can_save_lines(session):
    new_line = model.OrderLine("order1", "DECORATIVE-WIDGET", 12)
    session.add(new_line)
    session.commit()

    rows = list(session.execute('SELECT reference, sku, quantity FROM "order_lines"'))
    assert rows == [("order1", "DECORATIVE-WIDGET", 12)]


def test_retrieving_batches(session):
    session.execute(
        "INSERT INTO batches (reference, sku, quantity, eta)"
        ' VALUES ("batch1", "sku1", 100, null)'
    )
    session.execute(
        "INSERT INTO batches (reference, sku, quantity, eta)"
        ' VALUES ("batch2", "sku2", 200, "2011-04-11")'
    )
    expected = [
        model.Batch("batch1", "sku1", 100, eta=None),
        model.Batch("batch2", "sku2", 200, eta=date(2011, 4, 11)),
    ]

    assert session.query(model.Batch).all() == expected


def test_saving_batches(session):
    batch = model.Batch("batch1", "sku1", 100, eta=None)
    session.add(batch)
    session.commit()
    rows = session.execute(
        'SELECT reference, sku, quantity, eta FROM "batches"'
    )
    assert list(rows) == [("batch1", "sku1", 100, None)]


def test_savingallocated_orders(session):
    batch = model.Batch("batch1", "sku1", 100, eta=None)
    line = model.OrderLine("order1", "sku1", 10)
    batch.allocate(line)
    session.add(batch)
    session.commit()
    rows = list(session.execute('SELECT order_id, batch_id FROM "allocations"'))
    assert rows == [(batch.id, line.id)]


def test_retrievingallocated_orders(session):
    session.execute(
        'INSERT INTO order_lines (reference, sku, quantity) VALUES ("order1", "sku1", 12)'
    )
    [[olid]] = session.execute(
        "SELECT id FROM order_lines WHERE reference=:reference AND sku=:sku",
        dict(reference="order1", sku="sku1"),
    )
    session.execute(
        "INSERT INTO batches (reference, sku, quantity, eta)"
        ' VALUES ("batch1", "sku1", 100, null)'
    )
    [[bid]] = session.execute(
        "SELECT id FROM batches WHERE reference=:ref AND sku=:sku",
        dict(ref="batch1", sku="sku1"),
    )
    session.execute(
        "INSERT INTO allocations (order_id, batch_id) VALUES (:olid, :bid)",
        dict(olid=olid, bid=bid),
    )

    batch = session.query(model.Batch).one()

    assert batch.allocated_orders == {model.OrderLine("order1", "sku1", 12)}

from allocation.domain import model, events


def test_product_records_out_of_stock_events():
    batch = model.Batch("b1","LAMP",10)
    product = model.Product("LAMP", [batch])
    product.allocate(model.OrderLine("order1","LAMP",10))

    allocation = product.allocate(model.OrderLine("order2","LAMP",10))
    assert product.events[-1] == events.OutOfStock(sku="LAMP")
    assert allocation is None
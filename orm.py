import model
from sqlalchemy import Table, Column, Integer, String, DateTime
from sqlalchemy.orm import mapper, relationship


order_lines = Table(
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("reference", String(255)),
    Column("sku", String(255)),
    Column("quantity", Integer, nullable=False)
)

batches = Table(
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("reference", String(255)),
    Column("sku", String(255)),
    Column("quantity", Integer, nullable=False),
    Column("eta", DateTime)
)

allocations = Table(
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("order_id", Integer),
    Column("batch_id", Integer),
)

def start_mappers():
    lines = mapper(model.OrderLine, order_lines)
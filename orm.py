import model
from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey, MetaData
from sqlalchemy.orm import mapper, relationship 

metadata = MetaData()

order_lines = Table(
    "order_lines",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("reference", String(255)),
    Column("sku", String(255)),
    Column("quantity", Integer, nullable=False)
)

batches = Table(
    "batches",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("reference", String(255)),
    Column("sku", String(255)),
    Column("quantity", Integer, nullable=False),
    Column("eta", DateTime)
)

allocations = Table(
    "allocations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("order_id", ForeignKey("order_lines.id")),
    Column("batch_id", ForeignKey("batches.id"))
)

def start_mappers():
    lines_mapper = mapper(model.OrderLine, order_lines)
    mapper(
        model.Batch,
        batches,
        properties={
            "allocated_orders": relationship(
                lines_mapper, secondary=allocations, collection_class=set,
            )
        },
    )
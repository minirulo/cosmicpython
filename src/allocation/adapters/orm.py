<<<<<<< HEAD:adapters/orm.py
import domain.model as model
from sqlalchemy import Table, Column, Integer, String, Date, ForeignKey, MetaData
from sqlalchemy.orm import mapper, relationship 
=======
from sqlalchemy import Table, MetaData, Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import mapper, relationship

from allocation.domain import model
>>>>>>> chapter_06_uow_exercise:src/allocation/adapters/orm.py


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
    Column("eta", Date)
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
<<<<<<< HEAD:adapters/orm.py
            "allocated_orders": relationship(
                lines_mapper, secondary=allocations, collection_class=set,
=======
            "_allocations": relationship(
                lines_mapper,
                secondary=allocations,
                collection_class=set,
>>>>>>> chapter_06_uow_exercise:src/allocation/adapters/orm.py
            )
        },
    )

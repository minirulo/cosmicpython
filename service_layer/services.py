from __future__ import annotations

import domain.model as model
from domain.model import OrderLine
from adapters.repository import AbstractRepository
from typing import Optional
from datetime import date

class InvalidSku(Exception):
    pass

class NotFoundError(Exception):
    pass

def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}

def add_batch(reference: str, sku: str, quantity: int, eta: date, repo: AbstractRepository, session) -> model.Batch:
    batchref = repo.add(model.Batch(reference, sku, quantity, eta))
    session.commit()
    return batchref

def allocate(line: OrderLine, repo: AbstractRepository, session) -> str:
    batches = repo.list()
    if not is_valid_sku(line.sku, batches):
        raise InvalidSku(f"Invalid sku {line.sku}")
    batchref = model.allocate(line, batches)
    session.commit()
    return batchref

def deallocate(line: OrderLine, reference: str, repo: AbstractRepository, session) -> str:
    batch = repo.get(reference)
    if not batch:
        raise InvalidSku(f"Batch {reference} not found")
    batch.deallocate(line)
    session.commit()
    return batch.reference
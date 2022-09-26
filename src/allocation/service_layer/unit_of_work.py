# pylint: disable=attribute-defined-outside-init
from __future__ import annotations
import abc
from typing import ContextManager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session

from allocation import config
from allocation.adapters import repository


class AbstractUnitOfWork(abc.ABC):
    batches: repository.AbstractRepository

    @abc.abstractmethod
    def commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        raise NotImplementedError

    def __exit__(self, *args):
        self.rollback()


DEFAULT_SESSION_FACTORY = sessionmaker(
    bind=create_engine(
        config.get_postgres_uri(),
    )
)


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory = DEFAULT_SESSION_FACTORY) -> None:
        self.session_factory = session_factory

    def __enter__(self):
        self.session = self.session_factory()
        self.batches = repository.SqlAlchemyRepository(self.session)
        return super().__enter__()
        
    def commit(self):
        self.session.commit()
        
    def rollback(self):
        self.session.rollback()
    
    def __exit__(self, *args):
        super().__exit__(*args)
        self.session.close()

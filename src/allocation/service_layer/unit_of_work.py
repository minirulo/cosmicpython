# pylint: disable=attribute-defined-outside-init
from __future__ import annotations
import abc
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session

from allocation import config
from allocation.adapters import repository

# from . import messagebus

class AbstractUnitOfWork(abc.ABC):
    products: repository.AbstractRepository

    def __enter__(self):
        return self

    def commit(self):
        self._commit()
        # self.publish_events()

    #! Before the UoW published to the messagebus
    # def publish_events(self):
    #     for product in self.products.seen:
    #         while product.events:
    #             event = product.events.pop(0)
    #             messagebus.handle(event)

    #! Now the messagebus polls from the UoW
    def collect_new_events(self):
        for product in self.products.seen:
            while product.events:
                yield product.events.pop(0)

    @abc.abstractmethod
    def _commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        raise NotImplementedError

    def __exit__(self, *args):
        self.rollback() # This is nice, for the default behaviour is not to change anything


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
        self.products = repository.SqlAlchemyRepository(self.session)
        return super().__enter__()
        
    def _commit(self):
        self.session.commit()
        
    def rollback(self):
        self.session.rollback()
    
    def __exit__(self, *args):
        super().__exit__(*args)
        self.session.close()

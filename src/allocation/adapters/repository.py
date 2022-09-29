import abc
from allocation.domain import model
from . import orm

class AbstractRepository(abc.ABC):
    def __init__(self):
        self.seen = set() # type: Set[model.Product]

    def add(self, product: model.Product):
        self._add(product)
        self.seen.add(product)

    def get(self, sku: str):
        product = self._get(sku)
        if product:
            self.seen.add(product)
        return product

    def get_by_batchref(self, ref: str):
        product = self._get_by_batchref(ref)
        if product:
            self.seen.add(product)
        return product

    @abc.abstractmethod
    def _add(self, product: model.Product):
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self, sku) -> model.Product:
        raise NotImplementedError
    
    @abc.abstractmethod
    def _get_by_batchref(self, sku) -> model.Product:
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, product):
        self.session.add(product)

    def _get(self, sku):
        return self.session.query(model.Product).filter_by(sku=sku).first()

    def _get_by_batchref(self, ref: str):
        return self.session.query(model.Product).join(model.Batch).filter(orm.batches.c.reference == ref).first()

    def list(self):
        return self.session.query(model.Product).all()

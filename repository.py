import abc
import model
from typing import List


class AbstractRepository(abc.ABC):
    @abc.abstractclassmethod
    def add(self, batch: model.Batch):
        raise NotImplementedError
    
    @abc.abstractclassmethod
    def get(self, reference) -> model.Batch:
        raise NotImplementedError


class SqlAlchemyRepository(abc.ABC):
    def __init__(self, session) -> None:
        self.session = session

    def commit(self):
        self.session.commit()

    def add(self, batch: model.Batch):
        self.session.add(batch)
    
    def get(self, reference) -> model.Batch:
        return self.session.query(model.Batch).filter_by(reference=reference).one()

    def list(self) -> List[model.Batch]:
        return self.session.query(model.Batch).all()
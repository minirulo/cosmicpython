import abc
import model


class AbstractRepository(abc.ABC):
    @abc.abstractclassmethod
    def add(self, batch: model.Batch):
        raise NotImplementedError
    
    @abc.abstractclassmethod
    def get(self, reference) -> model.Batch:
        raise NotImplementedError
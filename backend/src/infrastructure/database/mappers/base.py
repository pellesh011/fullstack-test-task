from abc import ABC, abstractmethod
from typing import Generic, TypeVar


EntityT = TypeVar("EntityT")
ModelT = TypeVar("ModelT")


class Mapper(ABC, Generic[EntityT, ModelT]):

    @abstractmethod
    def to_entity(
        self,
        model: ModelT,
    ) -> EntityT:
        pass

    @abstractmethod
    def to_model(
        self,
        entity: EntityT,
    ) -> ModelT:
        pass
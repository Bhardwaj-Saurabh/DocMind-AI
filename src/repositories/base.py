"""
Repository pattern for data persistence abstraction.

Following Clean Architecture: Business logic never knows about specific databases.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from uuid import UUID

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    """
    Abstract repository for data persistence.

    Implements the Repository pattern to abstract persistence logic
    from domain/application layers.
    """

    @abstractmethod
    def save(self, entity: T) -> T:
        """
        Save an entity to the repository.

        Args:
            entity: Entity to save

        Returns:
            Saved entity with any generated fields populated
        """
        pass

    @abstractmethod
    def find(self, id: str) -> T | None:
        """
        Find an entity by ID.

        Args:
            id: Entity identifier

        Returns:
            Entity if found, None otherwise
        """
        pass

    @abstractmethod
    def find_all(self) -> list[T]:
        """
        Find all entities.

        Returns:
            List of all entities
        """
        pass

    @abstractmethod
    def delete(self, id: str) -> bool:
        """
        Delete an entity by ID.

        Args:
            id: Entity identifier

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    def bulk_insert(self, entities: list[T]) -> bool:
        """
        Insert multiple entities in a single operation.

        Args:
            entities: List of entities to insert

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def exists(self, id: str) -> bool:
        """
        Check if an entity exists.

        Args:
            id: Entity identifier

        Returns:
            True if entity exists
        """
        pass


class ExtractionResultRepository(Repository[T]):
    """Repository specifically for extraction results."""

    @abstractmethod
    def find_by_document_id(self, document_id: str) -> list[T]:
        """
        Find extraction results by document ID.

        Args:
            document_id: Document identifier

        Returns:
            List of extraction results for the document
        """
        pass

    @abstractmethod
    def find_recent(self, limit: int = 10) -> list[T]:
        """
        Find most recent extraction results.

        Args:
            limit: Maximum number of results to return

        Returns:
            List of recent extraction results
        """
        pass

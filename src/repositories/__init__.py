"""
Repository implementations for data persistence.

Following the Repository pattern: Domain logic is independent of persistence.
"""

from .base import Repository, ExtractionResultRepository

__all__ = [
    "Repository",
    "ExtractionResultRepository",
]

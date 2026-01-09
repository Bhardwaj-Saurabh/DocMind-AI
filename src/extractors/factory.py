"""
Factory for creating document extractors based on file type.
"""

from pathlib import Path
from enum import Enum

from .base import BaseExtractor
from ..models import DocumentFormat


class ExtractorFactory:
    """
    Factory for creating appropriate document extractors.

    Implements the Factory pattern to dynamically create extractors
    based on document format.
    """

    _extractors: dict[DocumentFormat, type[BaseExtractor]] = {}

    @classmethod
    def register(cls, format: DocumentFormat, extractor_class: type[BaseExtractor]) -> None:
        """
        Register an extractor class for a specific format.

        Args:
            format: Document format
            extractor_class: Extractor class to register
        """
        cls._extractors[format] = extractor_class

    @classmethod
    def create(cls, file_path: str) -> BaseExtractor:
        """
        Create an extractor for the given file.

        Args:
            file_path: Path to the document file

        Returns:
            Appropriate extractor instance

        Raises:
            ValueError: If file format is not supported
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        format = cls._detect_format(path)

        if format not in cls._extractors:
            raise ValueError(f"Unsupported format: {format}")

        extractor_class = cls._extractors[format]
        return extractor_class(file_path)

    @classmethod
    def _detect_format(cls, path: Path) -> DocumentFormat:
        """
        Detect document format from file extension.

        Args:
            path: Path to file

        Returns:
            DocumentFormat enum value
        """
        suffix = path.suffix.lower()

        format_map = {
            ".pdf": DocumentFormat.PDF,
            ".docx": DocumentFormat.DOCX,
            ".doc": DocumentFormat.DOCX,
            ".pptx": DocumentFormat.PPTX,
            ".ppt": DocumentFormat.PPTX,
        }

        return format_map.get(suffix, DocumentFormat.UNKNOWN)

    @classmethod
    def get_supported_formats(cls) -> list[DocumentFormat]:
        """
        Get list of supported document formats.

        Returns:
            List of supported DocumentFormat values
        """
        return list(cls._extractors.keys())

    @classmethod
    def is_supported(cls, file_path: str) -> bool:
        """
        Check if file format is supported.

        Args:
            file_path: Path to file

        Returns:
            True if format is supported
        """
        path = Path(file_path)
        format = cls._detect_format(path)
        return format in cls._extractors


def create_extractor(file_path: str) -> BaseExtractor:
    """
    Convenience function to create an extractor.

    Args:
        file_path: Path to document file

    Returns:
        Appropriate extractor instance
    """
    return ExtractorFactory.create(file_path)

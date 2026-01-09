"""
Custom exception hierarchy for DocMind-AI.

Following the principle: Graceful degradation with clear error categorization.
"""


class DocMindException(Exception):
    """Base exception for all DocMind-AI errors."""
    pass


class ConfigurationError(DocMindException):
    """Raised when configuration is invalid or missing."""
    pass


class DocumentProcessingError(DocMindException):
    """Raised when document processing fails."""
    pass


class ExtractionError(DocumentProcessingError):
    """Raised when content extraction fails."""
    pass


class ContentAnalysisError(DocumentProcessingError):
    """Raised when content analysis fails."""
    pass


class VisionAPIError(DocMindException):
    """Raised when Vision API calls fail."""
    pass


class UnsupportedFormatError(DocMindException):
    """Raised when document format is not supported."""
    pass


class ValidationError(DocMindException):
    """Raised when data validation fails."""
    pass

"""Custom exception classes for the application."""


class AnnotatorException(Exception):
    """Base exception class for the Universal Annotator."""
    pass


class FileOperationError(AnnotatorException):
    """Raised for errors during file operations like loading or saving."""
    pass


class ConversionError(AnnotatorException):
    """Raised for errors during format conversion."""
    pass
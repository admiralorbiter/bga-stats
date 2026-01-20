"""
Custom exceptions for parsers.
"""


class ParserError(Exception):
    """Base exception for all parser errors."""
    pass


class ValidationError(ParserError):
    """Raised when input data fails validation."""
    pass


class ParseError(ParserError):
    """Raised when parsing fails due to malformed input."""
    pass

"""Errors the calculation can raise.  Each one carries a message fit for the user."""


class DomainError(Exception):
    """Base class: the input cannot be analysed as it stands."""


class InvalidPatternError(DomainError):
    """The pattern itself is malformed (ragged columns, NaN, unordered angles...)."""


class InsufficientDataError(DomainError):
    """The pattern is valid but too small for the statistics that were asked for."""

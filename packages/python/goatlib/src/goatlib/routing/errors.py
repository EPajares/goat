class RoutingError(Exception):
    """Base exception for routing adapter failures."""

    pass


class ParsingError(RoutingError):
    """Raised when an API response cannot be parsed correctly."""

    pass

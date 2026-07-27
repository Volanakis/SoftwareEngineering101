class ServiceError(Exception):
    """Base class for service-layer errors; the blueprint layer maps these to HTTP responses."""


class ValidationError(ServiceError):
    """400: malformed or incomplete input."""


class AuthorizationError(ServiceError):
    """403: authenticated but not permitted to perform this action."""


class NotFoundError(ServiceError):
    """404: referenced resource does not exist."""


class ConflictError(ServiceError):
    """409: state or uniqueness conflict (invalid transition, duplicate name, frozen set, ...)."""

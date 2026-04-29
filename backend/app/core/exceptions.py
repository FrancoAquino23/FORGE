# ==================================================================
# EXCEPTIONS UTILITIES
# ==================================================================

from fastapi import HTTPException, status

# Exception (ForgeException) base class and specific exceptions for common error cases
class ForgeException(HTTPException):
    """Base for all domain-specific HTTP errors."""

# Exception (NotFoundError) for 404 resource not found
class NotFoundError(ForgeException):
    def __init__(self, resource: str) -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=f"{resource} not found")

# Exception (ConflictError) for 409 conflicts
class ConflictError(ForgeException):
    def __init__(self, detail: str) -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)

# Exception (UnauthorizedError) for 401 unauthorized access
class UnauthorizedError(ForgeException):
    def __init__(self, detail: str = "Invalid or expired credentials") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

# Exception (ForbiddenError) for 403 forbidden actions
class ForbiddenError(ForgeException):
    def __init__(self, detail: str) -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

# Exception (RateLimitError) for 429 too many requests
class RateLimitError(ForgeException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit: maximum 10 activities per hour",
        )

# Exception (InsufficientMaterialsError) for 422 when forging without enough materials
class InsufficientMaterialsError(ForgeException):
    def __init__(self, detail: str = "Insufficient materials to forge") -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )

# Exception (PrestigeNotAvailableError) for 422 when trying to prestige without meeting requirements
class PrestigeNotAvailableError(ForgeException):
    def __init__(self, threshold: int) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Prestige requires attribute level {threshold}",
        )

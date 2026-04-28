from fastapi import HTTPException, status


class ForgeException(HTTPException):
    """Base for all domain-specific HTTP errors."""


class NotFoundError(ForgeException):
    def __init__(self, resource: str) -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=f"{resource} not found")


class ConflictError(ForgeException):
    def __init__(self, detail: str) -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class UnauthorizedError(ForgeException):
    def __init__(self, detail: str = "Invalid or expired credentials") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenError(ForgeException):
    def __init__(self, detail: str) -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class RateLimitError(ForgeException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit: maximum 10 activities per hour",
        )


class InsufficientMaterialsError(ForgeException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Insufficient materials to forge",
        )


class PrestigeNotAvailableError(ForgeException):
    def __init__(self, threshold: int) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Prestige requires artifact level {threshold}",
        )

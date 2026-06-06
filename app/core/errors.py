from fastapi import HTTPException, status


class BakerProfitError(Exception):
    def __init__(self, code: str, message: str, details: dict | None = None, status_code: int = 400):
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)

    def to_dict(self) -> dict:
        return {"error": {"code": self.code, "message": self.message, "details": self.details}}


class NotFoundError(BakerProfitError):
    def __init__(self, entity: str, entity_id: str | int):
        super().__init__(
            code="NOT_FOUND",
            message=f"{entity} not found",
            details={"id": str(entity_id)},
            status_code=404,
        )


class TenantIsolationError(BakerProfitError):
    def __init__(self):
        super().__init__(
            code="FORBIDDEN",
            message="Access denied",
            status_code=403,
        )


class ValidationError(BakerProfitError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(code="VALIDATION_ERROR", message=message, details=details or {})


class LowMarginWarning(BakerProfitError):
    def __init__(self, desired: str, actual: str):
        super().__init__(
            code="LOW_MARGIN_WARNING",
            message="This quote is profitable but below your desired margin.",
            details={"desired_margin_percent": desired, "actual_margin_percent": actual},
        )


def raise_http(error: BakerProfitError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.to_dict())

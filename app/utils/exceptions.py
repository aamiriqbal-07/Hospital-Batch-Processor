from fastapi import HTTPException, status
from typing import List, Any


class ValidationException(HTTPException):
    def __init__(self, errors: List[dict]):
        detail = {"detail": errors}
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )


class BatchNotFoundException(HTTPException):
    def __init__(self, batch_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch with ID {batch_id} not found"
        )


class CSVValidationException(Exception):
    def __init__(self, errors: List[dict]):
        self.errors = errors
        super().__init__("CSV validation failed")

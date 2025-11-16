from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from app.models.enums import HospitalStatus, BatchProcessingStatus

# External API Schemas
class HospitalCreate(BaseModel):
    name: str = Field(..., min_length=1)
    address: str = Field(..., min_length=1)
    phone: Optional[str] = None
    creation_batch_id: Optional[str] = None


class HospitalUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    address: Optional[str] = Field(None, min_length=1)
    phone: Optional[str] = None


class Hospital(BaseModel):
    id: int
    name: str = Field(..., min_length=1)
    address: str = Field(..., min_length=1)
    phone: Optional[str] = None
    creation_batch_id: Optional[str] = None
    active: bool = True
    created_at: str


class ActivateResponse(BaseModel):
    activated_count: int
    message: str


class DeleteResponse(BaseModel):
    deleted_count: int
    message: str


# Internal Application Schemas
class HospitalRecord(BaseModel):
    row: int
    hospital_id: Optional[int] = None
    name: str
    address: str
    phone: Optional[str] = None
    status: HospitalStatus
    error_message: Optional[str] = None


class BatchData(BaseModel):
    batch_id: str
    total_hospitals: int
    processed_hospitals: int = 0
    failed_hospitals: int = 0
    processing_time_seconds: float = 0.0
    batch_activated: bool = False
    processing_status: BatchProcessingStatus = BatchProcessingStatus.PENDING
    hospitals: List[HospitalRecord] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class BatchUploadResponse(BaseModel):
    batch_id: str
    total_hospitals: int
    message: str
    status: BatchProcessingStatus


class BatchCompleteResponse(BaseModel):
    batch_id: str
    total_hospitals: int
    processed_hospitals: int
    failed_hospitals: int
    processing_time_seconds: float
    batch_activated: bool
    hospitals: List[HospitalRecord]


class BatchStatusResponse(BaseModel):
    batch_id: str
    total_hospitals: int
    processed_hospitals: int
    failed_hospitals: int
    deleted_hospitals: int
    batch_activated: bool
    processing_status: BatchProcessingStatus
    hospitals: List[HospitalRecord]


class BatchProgressResponse(BaseModel):
    batch_id: str
    progress_percentage: float
    processing_status: BatchProcessingStatus
    processed_hospitals: int
    total_hospitals: int
    failed_hospitals: int
    current_message: str


class ValidationErrorDetail(BaseModel):
    loc: List[str | int]
    msg: str
    type: str


class HTTPValidationError(BaseModel):
    detail: List[ValidationErrorDetail]


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str

class ValidationErrorDetail(BaseModel):
    loc: List[str | int]
    msg: str
    type: str


class CSVValidationSuccessResponse(BaseModel):
    valid: bool = True
    message: str
    total_rows: int
    headers: List[str]


class CSVValidationErrorResponse(BaseModel):
    valid: bool = False
    message: str
    errors: List[ValidationErrorDetail]

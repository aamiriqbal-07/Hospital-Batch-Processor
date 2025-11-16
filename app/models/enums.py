from enum import Enum

class HospitalStatus(str, Enum):
    CREATED_AND_ACTIVATED = "created_and_activated"
    CREATED = "created"
    FAILED = "failed"
    DELETED = "deleted"


class BatchProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"

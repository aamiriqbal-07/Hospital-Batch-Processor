from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.models.schemas import (
    BatchUploadResponse, BatchStatusResponse, 
    BatchProgressResponse, HTTPValidationError
)
from app.services.batch_service import batch_service
from app.utils.exceptions import CSVValidationException, BatchNotFoundException

router = APIRouter(prefix="/batch", tags=["Batch Operations"])


@router.post(
    "/upload-csv",
    response_model=BatchUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        422: {"model": HTTPValidationError}
    },
    summary="Upload CSV and initiate hospital creation",
    description="Upload a CSV file to initiate bulk hospital creation. Returns batch_id immediately for progress tracking."
)
async def upload_csv(
    file: UploadFile = File(..., description="CSV file with columns: name,address,phone")
):
    # Validate file
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "detail": [{
                    "loc": ["file", "filename"],
                    "msg": "File must be a CSV file",
                    "type": "file_type_error"
                }]
            }
        )
    
    try:
        return await batch_service.initiate_csv_upload(file)
    except CSVValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"detail": e.errors}
        )


@router.get(
    "/{batch_id}/status",
    response_model=BatchStatusResponse,
    responses={
        404: {"description": "Batch not found"}
    },
    summary="Get batch status",
    description="Get current status of a batch with fresh data from external API"
)
async def get_batch_status(batch_id: str):
    try:
        return await batch_service.get_batch_status(batch_id)
    except BatchNotFoundException as e:
        raise e


@router.get(
    "/{batch_id}/progress",
    response_model=BatchProgressResponse,
    responses={
        404: {"description": "Batch not found"}
    },
    summary="Get batch processing progress (Polling endpoint)",
    description="Get real-time progress of batch processing. Poll this endpoint every 1-2 seconds."
)
async def get_batch_progress(batch_id: str):
    try:
        return await batch_service.get_batch_progress(batch_id)
    except BatchNotFoundException as e:
        raise e

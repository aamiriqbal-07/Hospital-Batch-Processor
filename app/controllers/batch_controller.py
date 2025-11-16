from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.models.schemas import (
    BatchUploadResponse, BatchStatusResponse, 
    BatchProgressResponse, HTTPValidationError,
    CSVValidationSuccessResponse, CSVValidationErrorResponse
)
from app.services.batch_service import batch_service
from app.utils.exceptions import CSVValidationException, BatchNotFoundException
from app.utils.csv_validator import CSVValidator

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
    description="Get real-time progress of batch processing."
)
async def get_batch_progress(batch_id: str):
    try:
        return await batch_service.get_batch_progress(batch_id)
    except BatchNotFoundException as e:
        raise e

@router.post(
    "/validate-csv",
    response_model=CSVValidationSuccessResponse,
    status_code=status.HTTP_200_OK,
    responses={
        422: {"model": CSVValidationErrorResponse}
    },
    summary="Validate CSV file without processing",
    description="Validate CSV structure and content."
)
async def validate_csv(
    file: UploadFile = File(..., description="CSV file with columns: name,address,phone")
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "valid": False,
                "message": "Invalid file type",
                "errors": [{
                    "loc": ["file", "filename"],
                    "msg": "File must be a CSV file",
                    "type": "file_type_error"
                }]
            }
        )
    
    try:
        csv_validator = CSVValidator()
        parsed_rows, _ = await csv_validator.validate_and_parse(file)
        
        return CSVValidationSuccessResponse(
            valid=True,
            message="CSV file is valid and ready for processing",
            total_rows=len(parsed_rows),
            headers=["name", "address", "phone"]
        )
    except CSVValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "valid": False,
                "message": "CSV validation failed",
                "errors": e.errors
            }
        )

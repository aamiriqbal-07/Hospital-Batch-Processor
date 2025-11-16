import uuid
import time
import asyncio
from typing import List, Dict
from datetime import datetime
from fastapi import UploadFile
from app.models.schemas import (
    BatchData, BatchUploadResponse, BatchStatusResponse,
    BatchProgressResponse, HospitalRecord, HospitalCreate,
    BatchCompleteResponse
)
from app.models.enums import HospitalStatus, BatchProcessingStatus
from app.repositories.batch_repository import batch_repository
from app.services.hospital_service import hospital_service
from app.utils.csv_validator import CSVValidator
from app.utils.exceptions import BatchNotFoundException, CSVValidationException


class BatchService:
    MAX_CONCURRENT_REQUESTS = 20
    
    def __init__(self):
        self.repository = batch_repository
        self.hospital_service = hospital_service
        self.csv_validator = CSVValidator()
    
    async def initiate_csv_upload(self, file: UploadFile) -> BatchUploadResponse:
        parsed_rows, _ = await self.csv_validator.validate_and_parse(file)

        batch_id = str(uuid.uuid4())

        batch_data = BatchData(
            batch_id=batch_id,
            total_hospitals=len(parsed_rows),
            processing_status=BatchProcessingStatus.PENDING
        )

        self.repository.save(batch_data)

        asyncio.create_task(self._process_batch_async(batch_id, parsed_rows))
        
        return BatchUploadResponse(
            batch_id=batch_id,
            total_hospitals=len(parsed_rows),
            message=f"CSV upload initiated. Use batch_id to track progress.",
            status=BatchProcessingStatus.PENDING
        )
    
    async def _process_batch_async(self, batch_id: str, parsed_rows: List[Dict[str, str]]):
        start_time = time.time()

        batch_data = self.repository.get(batch_id)
        batch_data.processing_status = BatchProcessingStatus.PROCESSING
        batch_data.started_at = datetime.utcnow()
        self.repository.save(batch_data)

        hospitals_records = await self._create_hospitals_parallel(
            parsed_rows, batch_id
        )
        

        processed_count = sum(
            1 for h in hospitals_records 
            if h.status == HospitalStatus.CREATED
        )
        failed_count = sum(
            1 for h in hospitals_records 
            if h.status == HospitalStatus.FAILED
        )

        batch_data.hospitals = hospitals_records
        batch_data.processed_hospitals = processed_count
        batch_data.failed_hospitals = failed_count
        self.repository.save(batch_data)

        batch_activated = False
        if processed_count > 0:
            activation_result = await self.hospital_service.activate_batch(batch_id)
            if activation_result and activation_result.activated_count > 0:
                batch_activated = True
                for hospital_record in hospitals_records:
                    if hospital_record.status == HospitalStatus.CREATED:
                        hospital_record.status = HospitalStatus.CREATED_AND_ACTIVATED
        
        processing_time = time.time() - start_time
        
        batch_data.batch_activated = batch_activated
        batch_data.processing_time_seconds = round(processing_time, 2)
        batch_data.processing_status = (
            BatchProcessingStatus.COMPLETED if failed_count == 0
            else BatchProcessingStatus.PARTIALLY_COMPLETED if processed_count > 0
            else BatchProcessingStatus.FAILED
        )
        batch_data.completed_at = datetime.utcnow()
        self.repository.save(batch_data)
    
    async def _create_hospitals_parallel(
        self, 
        parsed_rows: List[Dict[str, str]], 
        batch_id: str
    ) -> List[HospitalRecord]:
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_REQUESTS)
        
        async def create_with_semaphore(row: Dict[str, str], row_number: int):
            async with semaphore:
                return await self._create_hospital_from_row(row, row_number, batch_id)
        

        tasks = [
            create_with_semaphore(row, idx)
            for idx, row in enumerate(parsed_rows, start=1)
        ]

        hospitals_records = await asyncio.gather(*tasks)
        
        return list(hospitals_records)
    
    async def _create_hospital_from_row(
        self, 
        row: Dict[str, str], 
        row_number: int, 
        batch_id: str
    ) -> HospitalRecord:
        try:
            hospital_create = HospitalCreate(
                name=row['name'].strip(),
                address=row['address'].strip(),
                phone=row.get('phone'),
                creation_batch_id=batch_id
            )
            
            created_hospital = await self.hospital_service.create_hospital(
                hospital_create
            )
            
            if created_hospital:
                batch_data = self.repository.get(batch_id)
                if batch_data:
                    hospital_record = HospitalRecord(
                        row=row_number,
                        hospital_id=created_hospital.id,
                        name=created_hospital.name,
                        address=created_hospital.address,
                        phone=created_hospital.phone,
                        status=HospitalStatus.CREATED
                    )

                    batch_data.processed_hospitals = len([
                        h for h in batch_data.hospitals 
                        if h.status in [HospitalStatus.CREATED, HospitalStatus.CREATED_AND_ACTIVATED]
                    ]) + 1
                    self.repository.save(batch_data)
                    
                    return hospital_record
                else:
                    return HospitalRecord(
                        row=row_number,
                        hospital_id=created_hospital.id,
                        name=created_hospital.name,
                        address=created_hospital.address,
                        phone=created_hospital.phone,
                        status=HospitalStatus.CREATED
                    )
            else:
                # Update failed count
                batch_data = self.repository.get(batch_id)
                if batch_data:
                    batch_data.failed_hospitals += 1
                    self.repository.save(batch_data)
                
                return HospitalRecord(
                    row=row_number,
                    name=row['name'].strip(),
                    address=row['address'].strip(),
                    phone=row.get('phone'),
                    status=HospitalStatus.FAILED,
                    error_message="Failed to create hospital via external API"
                )
        except Exception as e:
            # Update failed count
            batch_data = self.repository.get(batch_id)
            if batch_data:
                batch_data.failed_hospitals += 1
                self.repository.save(batch_data)
            
            return HospitalRecord(
                row=row_number,
                name=row.get('name', '').strip(),
                address=row.get('address', '').strip(),
                phone=row.get('phone'),
                status=HospitalStatus.FAILED,
                error_message=str(e)
            )
    
    async def get_batch_status(self, batch_id: str) -> BatchStatusResponse:
        batch_data = self.repository.get(batch_id)
        if not batch_data:
            raise BatchNotFoundException(batch_id)

        if batch_data.processing_status in [
            BatchProcessingStatus.COMPLETED, 
            BatchProcessingStatus.PARTIALLY_COMPLETED
        ]:
            external_hospitals = await self.hospital_service.get_hospitals_by_batch(batch_id)
            external_hospitals_map = {h.id: h for h in external_hospitals}
            
            deleted_count = 0
            for hospital_record in batch_data.hospitals:
                if hospital_record.hospital_id:
                    external_hospital = external_hospitals_map.get(hospital_record.hospital_id)
                    
                    if not external_hospital:
                        if hospital_record.status != HospitalStatus.DELETED:
                            hospital_record.status = HospitalStatus.DELETED
                            deleted_count += 1
                    else:
                        if external_hospital.active:
                            if hospital_record.status != HospitalStatus.DELETED:
                                hospital_record.status = HospitalStatus.CREATED_AND_ACTIVATED
                        else:
                            if hospital_record.status not in [HospitalStatus.DELETED, HospitalStatus.FAILED]:
                                hospital_record.status = HospitalStatus.CREATED
            
            self.repository.save(batch_data)
        else:
            deleted_count = len([
                h for h in batch_data.hospitals 
                if h.status == HospitalStatus.DELETED
            ])
        
        return BatchStatusResponse(
            batch_id=batch_id,
            total_hospitals=batch_data.total_hospitals,
            processed_hospitals=batch_data.processed_hospitals,
            failed_hospitals=batch_data.failed_hospitals,
            deleted_hospitals=deleted_count,
            batch_activated=batch_data.batch_activated,
            processing_status=batch_data.processing_status,
            hospitals=batch_data.hospitals
        )
    
    async def get_batch_progress(self, batch_id: str) -> BatchProgressResponse:
        batch_data = self.repository.get(batch_id)
        if not batch_data:
            raise BatchNotFoundException(batch_id)
        
        total = batch_data.total_hospitals
        processed = batch_data.processed_hospitals + batch_data.failed_hospitals
        progress_percentage = (processed / total * 100) if total > 0 else 0
        
        if batch_data.processing_status == BatchProcessingStatus.PENDING:
            current_message = "Batch processing queued"
        elif batch_data.processing_status == BatchProcessingStatus.PROCESSING:
            current_message = f"Processing hospital {processed}/{total}"
        elif batch_data.processing_status == BatchProcessingStatus.COMPLETED:
            current_message = "All hospitals processed successfully"
        elif batch_data.processing_status == BatchProcessingStatus.PARTIALLY_COMPLETED:
            current_message = f"Completed with {batch_data.failed_hospitals} failures"
        elif batch_data.processing_status == BatchProcessingStatus.FAILED:
            current_message = "Processing failed"
        else:
            current_message = "Unknown status"
        
        return BatchProgressResponse(
            batch_id=batch_id,
            progress_percentage=round(progress_percentage, 2),
            processing_status=batch_data.processing_status,
            processed_hospitals=processed,
            total_hospitals=total,
            failed_hospitals=batch_data.failed_hospitals,
            current_message=current_message
        )

# Singleton instance
batch_service = BatchService()

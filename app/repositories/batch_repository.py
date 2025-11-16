from typing import Dict, Optional, List
from app.models.schemas import BatchData, HospitalRecord
from app.models.enums import HospitalStatus


class BatchRepository:
    def __init__(self):
        self._storage: Dict[str, BatchData] = {}
    
    def save(self, batch_data: BatchData) -> BatchData:
        """Save or update batch data"""
        self._storage[batch_data.batch_id] = batch_data
        return batch_data
    
    def get(self, batch_id: str) -> Optional[BatchData]:
        """Get batch data by ID"""
        return self._storage.get(batch_id)
    
    def exists(self, batch_id: str) -> bool:
        """Check if batch exists"""
        return batch_id in self._storage
    
    def update_hospital_status(
        self, 
        batch_id: str, 
        hospital_id: int, 
        status: HospitalStatus
    ) -> bool:
        """Update hospital status in batch"""
        batch_data = self.get(batch_id)
        if not batch_data:
            return False
        
        for hospital in batch_data.hospitals:
            if hospital.hospital_id == hospital_id:
                hospital.status = status
                self.save(batch_data)
                return True
        
        return False
    
    def get_hospitals_by_status(
        self, 
        batch_id: str, 
        status: HospitalStatus
    ) -> List[HospitalRecord]:
        """Get hospitals by status in a batch"""
        batch_data = self.get(batch_id)
        if not batch_data:
            return []
        
        return [h for h in batch_data.hospitals if h.status == status]
    
    def delete(self, batch_id: str) -> bool:
        """Delete batch data"""
        if batch_id in self._storage:
            del self._storage[batch_id]
            return True
        return False


# Singleton instance
batch_repository = BatchRepository()

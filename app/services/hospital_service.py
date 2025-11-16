import httpx
from typing import List, Optional
from app.core.config import settings
from app.models.schemas import (
    Hospital, HospitalCreate, HospitalUpdate, 
    ActivateResponse, DeleteResponse
)


class HospitalService:
    def __init__(self):
        self.base_url = settings.EXTERNAL_API_BASE_URL
        self.timeout = 30.0
    
    async def create_hospital(self, hospital_data: HospitalCreate) -> Optional[Hospital]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/hospitals/",
                    json=hospital_data.model_dump(exclude_none=False),
                    headers={
                        "accept": "application/json",
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                return Hospital(**response.json())
            except Exception as e:
                return None
    
    async def get_hospital(self, hospital_id: int) -> Optional[Hospital]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/hospitals/{hospital_id}",
                    headers={"accept": "application/json"}
                )
                response.raise_for_status()
                return Hospital(**response.json())
            except Exception:
                return None
    
    async def get_hospitals_by_batch(self, batch_id: str) -> List[Hospital]:
        """Get all hospitals in a batch"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/hospitals/batch/{batch_id}",
                    headers={"accept": "application/json"}
                )
                response.raise_for_status()
                return [Hospital(**h) for h in response.json()]
            except Exception:
                return []
    
    async def activate_batch(self, batch_id: str) -> Optional[ActivateResponse]:
        """Activate all hospitals in a batch"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.patch(
                    f"{self.base_url}/hospitals/batch/{batch_id}/activate",
                    json={},
                    headers={
                        "accept": "application/json",
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                return ActivateResponse(**response.json())
            except Exception:
                return None
    
    async def update_hospital(
        self, 
        hospital_id: int, 
        hospital_data: HospitalUpdate
    ) -> Optional[Hospital]:
        """Update hospital"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.put(
                    f"{self.base_url}/hospitals/{hospital_id}",
                    json=hospital_data.model_dump(exclude_none=True),
                    headers={
                        "accept": "application/json",
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                return Hospital(**response.json())
            except Exception:
                return None
    
    async def delete_hospital(self, hospital_id: int) -> bool:
        """Delete hospital by ID"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.delete(
                    f"{self.base_url}/hospitals/{hospital_id}",
                    headers={"accept": "application/json"}
                )
                return response.status_code == 204
            except Exception:
                return False
    
    async def delete_batch(self, batch_id: str) -> Optional[DeleteResponse]:
        """Delete all hospitals in a batch"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.delete(
                    f"{self.base_url}/hospitals/batch/{batch_id}",
                    headers={"accept": "application/json"}
                )
                response.raise_for_status()
                return DeleteResponse(**response.json())
            except Exception:
                return None


# Singleton instance
hospital_service = HospitalService()

import json
import logging
from typing import List, Optional

from datetime import datetime, date

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.diet_plans import Diet_plansService
from dependencies.auth import get_current_user
from schemas.auth import UserResponse
from dependencies.database import DbSession

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/entities/diet_plans", tags=["diet_plans"])


# ---------- Pydantic Schemas ----------
class Diet_plansData(BaseModel):
    """Entity data schema (for create/update)"""
    height: float
    weight: float
    age: int
    sex: str
    activity_level: str
    goal: str = None
    daily_calories: int = None
    plan_text: str = None
    workout_text: str = None
    created_at: Optional[datetime] = None


class Diet_plansUpdateData(BaseModel):
    """Update entity data (partial updates allowed)"""
    height: Optional[float] = None
    weight: Optional[float] = None
    age: Optional[int] = None
    sex: Optional[str] = None
    activity_level: Optional[str] = None
    goal: Optional[str] = None
    daily_calories: Optional[int] = None
    plan_text: Optional[str] = None
    workout_text: Optional[str] = None
    created_at: Optional[datetime] = None


class Diet_plansResponse(BaseModel):
    """Entity response schema"""
    id: int
    user_id: str
    height: float
    weight: float
    age: int
    sex: str
    activity_level: str
    goal: Optional[str] = None
    daily_calories: Optional[int] = None
    plan_text: Optional[str] = None
    workout_text: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Diet_plansListResponse(BaseModel):
    """List response schema"""
    items: List[Diet_plansResponse]
    total: int
    skip: int
    limit: int


class Diet_plansBatchCreateRequest(BaseModel):
    """Batch create request"""
    items: List[Diet_plansData]


class Diet_plansBatchUpdateItem(BaseModel):
    """Batch update item"""
    id: int
    updates: Diet_plansUpdateData


class Diet_plansBatchUpdateRequest(BaseModel):
    """Batch update request"""
    items: List[Diet_plansBatchUpdateItem]


class Diet_plansBatchDeleteRequest(BaseModel):
    """Batch delete request"""
    ids: List[int]


# ---------- Routes ----------
@router.get("", response_model=Diet_plansListResponse)
async def query_diet_planss(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Query diet_planss with filtering, sorting, and pagination (user can only see their own records)"""
    logger.debug(f"Querying diet_planss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")
    
    service = Diet_plansService(db)
    try:
        # Parse query JSON if provided
        query_dict = None
        if query:
            try:
                query_dict = json.loads(query)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid query JSON format")
        
        result = await service.get_list(
            skip=skip, 
            limit=limit,
            query_dict=query_dict,
            sort=sort,
            user_id=str(current_user.id),
        )
        logger.debug(f"Found {result['total']} diet_planss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying diet_planss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/all", response_model=Diet_plansListResponse)
async def query_diet_planss_all(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    # Query diet_planss with filtering, sorting, and pagination without user limitation
    logger.debug(f"Querying diet_planss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")

    service = Diet_plansService(db)
    try:
        # Parse query JSON if provided
        query_dict = None
        if query:
            try:
                query_dict = json.loads(query)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid query JSON format")

        result = await service.get_list(
            skip=skip,
            limit=limit,
            query_dict=query_dict,
            sort=sort
        )
        logger.debug(f"Found {result['total']} diet_planss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying diet_planss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{id}", response_model=Diet_plansResponse)
async def get_diet_plans(
    id: int,
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single diet_plans by ID (user can only see their own records)"""
    logger.debug(f"Fetching diet_plans with id: {id}, fields={fields}")
    
    service = Diet_plansService(db)
    try:
        result = await service.get_by_id(id, user_id=str(current_user.id))
        if not result:
            logger.warning(f"Diet_plans with id {id} not found")
            raise HTTPException(status_code=404, detail="Diet_plans not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching diet_plans {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("", response_model=Diet_plansResponse, status_code=201)
async def create_diet_plans(
    data: Diet_plansData,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new diet_plans"""
    logger.debug(f"Creating new diet_plans with data: {data}")
    
    service = Diet_plansService(db)
    try:
        result = await service.create(data.model_dump(), user_id=str(current_user.id))
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create diet_plans")
        
        logger.info(f"Diet_plans created successfully with id: {result.id}")
        return result
    except ValueError as e:
        logger.error(f"Validation error creating diet_plans: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating diet_plans: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/batch", response_model=List[Diet_plansResponse], status_code=201)
async def create_diet_planss_batch(
    request: Diet_plansBatchCreateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create multiple diet_planss in a single request"""
    logger.debug(f"Batch creating {len(request.items)} diet_planss")
    
    service = Diet_plansService(db)
    results = []
    
    try:
        for item_data in request.items:
            result = await service.create(item_data.model_dump(), user_id=str(current_user.id))
            if result:
                results.append(result)
        
        logger.info(f"Batch created {len(results)} diet_planss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch create: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch create failed: {str(e)}")


@router.put("/batch", response_model=List[Diet_plansResponse])
async def update_diet_planss_batch(
    request: Diet_plansBatchUpdateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update multiple diet_planss in a single request (requires ownership)"""
    logger.debug(f"Batch updating {len(request.items)} diet_planss")
    
    service = Diet_plansService(db)
    results = []
    
    try:
        for item in request.items:
            # Only include non-None values for partial updates
            update_dict = {k: v for k, v in item.updates.model_dump().items() if v is not None}
            result = await service.update(item.id, update_dict, user_id=str(current_user.id))
            if result:
                results.append(result)
        
        logger.info(f"Batch updated {len(results)} diet_planss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch update failed: {str(e)}")


@router.put("/{id}", response_model=Diet_plansResponse)
async def update_diet_plans(
    id: int,
    data: Diet_plansUpdateData,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing diet_plans (requires ownership)"""
    logger.debug(f"Updating diet_plans {id} with data: {data}")

    service = Diet_plansService(db)
    try:
        # Only include non-None values for partial updates
        update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
        result = await service.update(id, update_dict, user_id=str(current_user.id))
        if not result:
            logger.warning(f"Diet_plans with id {id} not found for update")
            raise HTTPException(status_code=404, detail="Diet_plans not found")
        
        logger.info(f"Diet_plans {id} updated successfully")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating diet_plans {id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating diet_plans {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/batch")
async def delete_diet_planss_batch(
    request: Diet_plansBatchDeleteRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete multiple diet_planss by their IDs (requires ownership)"""
    logger.debug(f"Batch deleting {len(request.ids)} diet_planss")
    
    service = Diet_plansService(db)
    deleted_count = 0
    
    try:
        for item_id in request.ids:
            success = await service.delete(item_id, user_id=str(current_user.id))
            if success:
                deleted_count += 1
        
        logger.info(f"Batch deleted {deleted_count} diet_planss successfully")
        return {"message": f"Successfully deleted {deleted_count} diet_planss", "deleted_count": deleted_count}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch delete: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch delete failed: {str(e)}")


@router.delete("/{id}")
async def delete_diet_plans(
    id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a single diet_plans by ID (requires ownership)"""
    logger.debug(f"Deleting diet_plans with id: {id}")
    
    service = Diet_plansService(db)
    try:
        success = await service.delete(id, user_id=str(current_user.id))
        if not success:
            logger.warning(f"Diet_plans with id {id} not found for deletion")
            raise HTTPException(status_code=404, detail="Diet_plans not found")
        
        logger.info(f"Diet_plans {id} deleted successfully")
        return {"message": "Diet_plans deleted successfully", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting diet_plans {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
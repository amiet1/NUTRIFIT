import json
import logging
from typing import List, Optional

from datetime import datetime, date

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.meal_logs import Meal_logsService
from dependencies.auth import get_current_user
from schemas.auth import UserResponse

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/entities/meal_logs", tags=["meal_logs"])


# ---------- Pydantic Schemas ----------
class Meal_logsData(BaseModel):
    """Entity data schema (for create/update)"""
    diet_plan_id: int = None
    date: str
    meal_type: str
    description: str
    calories: int
    image_key: str = None
    from_plan: bool = None
    created_at: Optional[datetime] = None


class Meal_logsUpdateData(BaseModel):
    """Update entity data (partial updates allowed)"""
    diet_plan_id: Optional[int] = None
    date: Optional[str] = None
    meal_type: Optional[str] = None
    description: Optional[str] = None
    calories: Optional[int] = None
    image_key: Optional[str] = None
    from_plan: Optional[bool] = None
    created_at: Optional[datetime] = None


class Meal_logsResponse(BaseModel):
    """Entity response schema"""
    id: int
    user_id: str
    diet_plan_id: Optional[int] = None
    date: str
    meal_type: str
    description: str
    calories: int
    image_key: Optional[str] = None
    from_plan: Optional[bool] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Meal_logsListResponse(BaseModel):
    """List response schema"""
    items: List[Meal_logsResponse]
    total: int
    skip: int
    limit: int


class Meal_logsBatchCreateRequest(BaseModel):
    """Batch create request"""
    items: List[Meal_logsData]


class Meal_logsBatchUpdateItem(BaseModel):
    """Batch update item"""
    id: int
    updates: Meal_logsUpdateData


class Meal_logsBatchUpdateRequest(BaseModel):
    """Batch update request"""
    items: List[Meal_logsBatchUpdateItem]


class Meal_logsBatchDeleteRequest(BaseModel):
    """Batch delete request"""
    ids: List[int]


# ---------- Routes ----------
@router.get("", response_model=Meal_logsListResponse)
async def query_meal_logss(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Query meal_logss with filtering, sorting, and pagination (user can only see their own records)"""
    logger.debug(f"Querying meal_logss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")
    
    service = Meal_logsService(db)
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
        logger.debug(f"Found {result['total']} meal_logss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying meal_logss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/all", response_model=Meal_logsListResponse)
async def query_meal_logss_all(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    # Query meal_logss with filtering, sorting, and pagination without user limitation
    logger.debug(f"Querying meal_logss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")

    service = Meal_logsService(db)
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
        logger.debug(f"Found {result['total']} meal_logss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying meal_logss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{id}", response_model=Meal_logsResponse)
async def get_meal_logs(
    id: int,
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single meal_logs by ID (user can only see their own records)"""
    logger.debug(f"Fetching meal_logs with id: {id}, fields={fields}")
    
    service = Meal_logsService(db)
    try:
        result = await service.get_by_id(id, user_id=str(current_user.id))
        if not result:
            logger.warning(f"Meal_logs with id {id} not found")
            raise HTTPException(status_code=404, detail="Meal_logs not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching meal_logs {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("", response_model=Meal_logsResponse, status_code=201)
async def create_meal_logs(
    data: Meal_logsData,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new meal_logs"""
    logger.debug(f"Creating new meal_logs with data: {data}")
    
    service = Meal_logsService(db)
    try:
        result = await service.create(data.model_dump(), user_id=str(current_user.id))
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create meal_logs")
        
        logger.info(f"Meal_logs created successfully with id: {result.id}")
        return result
    except ValueError as e:
        logger.error(f"Validation error creating meal_logs: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating meal_logs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/batch", response_model=List[Meal_logsResponse], status_code=201)
async def create_meal_logss_batch(
    request: Meal_logsBatchCreateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create multiple meal_logss in a single request"""
    logger.debug(f"Batch creating {len(request.items)} meal_logss")
    
    service = Meal_logsService(db)
    results = []
    
    try:
        for item_data in request.items:
            result = await service.create(item_data.model_dump(), user_id=str(current_user.id))
            if result:
                results.append(result)
        
        logger.info(f"Batch created {len(results)} meal_logss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch create: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch create failed: {str(e)}")


@router.put("/batch", response_model=List[Meal_logsResponse])
async def update_meal_logss_batch(
    request: Meal_logsBatchUpdateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update multiple meal_logss in a single request (requires ownership)"""
    logger.debug(f"Batch updating {len(request.items)} meal_logss")
    
    service = Meal_logsService(db)
    results = []
    
    try:
        for item in request.items:
            # Only include non-None values for partial updates
            update_dict = {k: v for k, v in item.updates.model_dump().items() if v is not None}
            result = await service.update(item.id, update_dict, user_id=str(current_user.id))
            if result:
                results.append(result)
        
        logger.info(f"Batch updated {len(results)} meal_logss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch update failed: {str(e)}")


@router.put("/{id}", response_model=Meal_logsResponse)
async def update_meal_logs(
    id: int,
    data: Meal_logsUpdateData,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing meal_logs (requires ownership)"""
    logger.debug(f"Updating meal_logs {id} with data: {data}")

    service = Meal_logsService(db)
    try:
        # Only include non-None values for partial updates
        update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
        result = await service.update(id, update_dict, user_id=str(current_user.id))
        if not result:
            logger.warning(f"Meal_logs with id {id} not found for update")
            raise HTTPException(status_code=404, detail="Meal_logs not found")
        
        logger.info(f"Meal_logs {id} updated successfully")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating meal_logs {id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating meal_logs {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/batch")
async def delete_meal_logss_batch(
    request: Meal_logsBatchDeleteRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete multiple meal_logss by their IDs (requires ownership)"""
    logger.debug(f"Batch deleting {len(request.ids)} meal_logss")
    
    service = Meal_logsService(db)
    deleted_count = 0
    
    try:
        for item_id in request.ids:
            success = await service.delete(item_id, user_id=str(current_user.id))
            if success:
                deleted_count += 1
        
        logger.info(f"Batch deleted {deleted_count} meal_logss successfully")
        return {"message": f"Successfully deleted {deleted_count} meal_logss", "deleted_count": deleted_count}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch delete: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch delete failed: {str(e)}")


@router.delete("/{id}")
async def delete_meal_logs(
    id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a single meal_logs by ID (requires ownership)"""
    logger.debug(f"Deleting meal_logs with id: {id}")
    
    service = Meal_logsService(db)
    try:
        success = await service.delete(id, user_id=str(current_user.id))
        if not success:
            logger.warning(f"Meal_logs with id {id} not found for deletion")
            raise HTTPException(status_code=404, detail="Meal_logs not found")
        
        logger.info(f"Meal_logs {id} deleted successfully")
        return {"message": "Meal_logs deleted successfully", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting meal_logs {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
import json
import logging
from typing import List, Optional

from datetime import datetime, date

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.weight_entries import Weight_entriesService
from dependencies.auth import get_current_user
from schemas.auth import UserResponse

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/entities/weight_entries", tags=["weight_entries"])


# ---------- Pydantic Schemas ----------
class Weight_entriesData(BaseModel):
    """Entity data schema (for create/update)"""
    date: str
    weight_kg: float
    note: str = None
    image_key: str = None
    created_at: Optional[datetime] = None


class Weight_entriesUpdateData(BaseModel):
    """Update entity data (partial updates allowed)"""
    date: Optional[str] = None
    weight_kg: Optional[float] = None
    note: Optional[str] = None
    image_key: Optional[str] = None
    created_at: Optional[datetime] = None


class Weight_entriesResponse(BaseModel):
    """Entity response schema"""
    id: int
    user_id: str
    date: str
    weight_kg: float
    note: Optional[str] = None
    image_key: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Weight_entriesListResponse(BaseModel):
    """List response schema"""
    items: List[Weight_entriesResponse]
    total: int
    skip: int
    limit: int


class Weight_entriesBatchCreateRequest(BaseModel):
    """Batch create request"""
    items: List[Weight_entriesData]


class Weight_entriesBatchUpdateItem(BaseModel):
    """Batch update item"""
    id: int
    updates: Weight_entriesUpdateData


class Weight_entriesBatchUpdateRequest(BaseModel):
    """Batch update request"""
    items: List[Weight_entriesBatchUpdateItem]


class Weight_entriesBatchDeleteRequest(BaseModel):
    """Batch delete request"""
    ids: List[int]


# ---------- Routes ----------
@router.get("", response_model=Weight_entriesListResponse)
async def query_weight_entriess(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Query weight_entriess with filtering, sorting, and pagination (user can only see their own records)"""
    logger.debug(f"Querying weight_entriess: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")
    
    service = Weight_entriesService(db)
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
        logger.debug(f"Found {result['total']} weight_entriess")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying weight_entriess: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/all", response_model=Weight_entriesListResponse)
async def query_weight_entriess_all(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    # Query weight_entriess with filtering, sorting, and pagination without user limitation
    logger.debug(f"Querying weight_entriess: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")

    service = Weight_entriesService(db)
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
        logger.debug(f"Found {result['total']} weight_entriess")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying weight_entriess: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{id}", response_model=Weight_entriesResponse)
async def get_weight_entries(
    id: int,
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single weight_entries by ID (user can only see their own records)"""
    logger.debug(f"Fetching weight_entries with id: {id}, fields={fields}")
    
    service = Weight_entriesService(db)
    try:
        result = await service.get_by_id(id, user_id=str(current_user.id))
        if not result:
            logger.warning(f"Weight_entries with id {id} not found")
            raise HTTPException(status_code=404, detail="Weight_entries not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching weight_entries {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("", response_model=Weight_entriesResponse, status_code=201)
async def create_weight_entries(
    data: Weight_entriesData,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new weight_entries"""
    logger.debug(f"Creating new weight_entries with data: {data}")
    
    service = Weight_entriesService(db)
    try:
        result = await service.create(data.model_dump(), user_id=str(current_user.id))
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create weight_entries")
        
        logger.info(f"Weight_entries created successfully with id: {result.id}")
        return result
    except ValueError as e:
        logger.error(f"Validation error creating weight_entries: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating weight_entries: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/batch", response_model=List[Weight_entriesResponse], status_code=201)
async def create_weight_entriess_batch(
    request: Weight_entriesBatchCreateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create multiple weight_entriess in a single request"""
    logger.debug(f"Batch creating {len(request.items)} weight_entriess")
    
    service = Weight_entriesService(db)
    results = []
    
    try:
        for item_data in request.items:
            result = await service.create(item_data.model_dump(), user_id=str(current_user.id))
            if result:
                results.append(result)
        
        logger.info(f"Batch created {len(results)} weight_entriess successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch create: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch create failed: {str(e)}")


@router.put("/batch", response_model=List[Weight_entriesResponse])
async def update_weight_entriess_batch(
    request: Weight_entriesBatchUpdateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update multiple weight_entriess in a single request (requires ownership)"""
    logger.debug(f"Batch updating {len(request.items)} weight_entriess")
    
    service = Weight_entriesService(db)
    results = []
    
    try:
        for item in request.items:
            # Only include non-None values for partial updates
            update_dict = {k: v for k, v in item.updates.model_dump().items() if v is not None}
            result = await service.update(item.id, update_dict, user_id=str(current_user.id))
            if result:
                results.append(result)
        
        logger.info(f"Batch updated {len(results)} weight_entriess successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch update failed: {str(e)}")


@router.put("/{id}", response_model=Weight_entriesResponse)
async def update_weight_entries(
    id: int,
    data: Weight_entriesUpdateData,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing weight_entries (requires ownership)"""
    logger.debug(f"Updating weight_entries {id} with data: {data}")

    service = Weight_entriesService(db)
    try:
        # Only include non-None values for partial updates
        update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
        result = await service.update(id, update_dict, user_id=str(current_user.id))
        if not result:
            logger.warning(f"Weight_entries with id {id} not found for update")
            raise HTTPException(status_code=404, detail="Weight_entries not found")
        
        logger.info(f"Weight_entries {id} updated successfully")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating weight_entries {id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating weight_entries {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/batch")
async def delete_weight_entriess_batch(
    request: Weight_entriesBatchDeleteRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete multiple weight_entriess by their IDs (requires ownership)"""
    logger.debug(f"Batch deleting {len(request.ids)} weight_entriess")
    
    service = Weight_entriesService(db)
    deleted_count = 0
    
    try:
        for item_id in request.ids:
            success = await service.delete(item_id, user_id=str(current_user.id))
            if success:
                deleted_count += 1
        
        logger.info(f"Batch deleted {deleted_count} weight_entriess successfully")
        return {"message": f"Successfully deleted {deleted_count} weight_entriess", "deleted_count": deleted_count}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch delete: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch delete failed: {str(e)}")


@router.delete("/{id}")
async def delete_weight_entries(
    id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a single weight_entries by ID (requires ownership)"""
    logger.debug(f"Deleting weight_entries with id: {id}")
    
    service = Weight_entriesService(db)
    try:
        success = await service.delete(id, user_id=str(current_user.id))
        if not success:
            logger.warning(f"Weight_entries with id {id} not found for deletion")
            raise HTTPException(status_code=404, detail="Weight_entries not found")
        
        logger.info(f"Weight_entries {id} deleted successfully")
        return {"message": "Weight_entries deleted successfully", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting weight_entries {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
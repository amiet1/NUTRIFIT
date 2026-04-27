import logging
from typing import Optional, Dict, Any, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.weight_entries import Weight_entries

logger = logging.getLogger(__name__)


# ------------------ Service Layer ------------------
class Weight_entriesService:
    """Service layer for Weight_entries operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: Dict[str, Any], user_id: Optional[str] = None) -> Optional[Weight_entries]:
        """Create a new weight_entries"""
        try:
            if user_id:
                data['user_id'] = user_id
            obj = Weight_entries(**data)
            self.db.add(obj)
            await self.db.commit()
            await self.db.refresh(obj)
            logger.info(f"Created weight_entries with id: {obj.id}")
            return obj
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating weight_entries: {str(e)}")
            raise

    async def check_ownership(self, obj_id: int, user_id: str) -> bool:
        """Check if user owns this record"""
        try:
            obj = await self.get_by_id(obj_id, user_id=user_id)
            return obj is not None
        except Exception as e:
            logger.error(f"Error checking ownership for weight_entries {obj_id}: {str(e)}")
            return False

    async def get_by_id(self, obj_id: int, user_id: Optional[str] = None) -> Optional[Weight_entries]:
        """Get weight_entries by ID (user can only see their own records)"""
        try:
            query = select(Weight_entries).where(Weight_entries.id == obj_id)
            if user_id:
                query = query.where(Weight_entries.user_id == user_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching weight_entries {obj_id}: {str(e)}")
            raise

    async def get_list(
        self, 
        skip: int = 0, 
        limit: int = 20, 
        user_id: Optional[str] = None,
        query_dict: Optional[Dict[str, Any]] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get paginated list of weight_entriess (user can only see their own records)"""
        try:
            query = select(Weight_entries)
            count_query = select(func.count(Weight_entries.id))
            
            if user_id:
                query = query.where(Weight_entries.user_id == user_id)
                count_query = count_query.where(Weight_entries.user_id == user_id)
            
            if query_dict:
                for field, value in query_dict.items():
                    if hasattr(Weight_entries, field):
                        query = query.where(getattr(Weight_entries, field) == value)
                        count_query = count_query.where(getattr(Weight_entries, field) == value)
            
            count_result = await self.db.execute(count_query)
            total = count_result.scalar()

            if sort:
                if sort.startswith('-'):
                    field_name = sort[1:]
                    if hasattr(Weight_entries, field_name):
                        query = query.order_by(getattr(Weight_entries, field_name).desc())
                else:
                    if hasattr(Weight_entries, sort):
                        query = query.order_by(getattr(Weight_entries, sort))
            else:
                query = query.order_by(Weight_entries.id.desc())

            result = await self.db.execute(query.offset(skip).limit(limit))
            items = result.scalars().all()

            return {
                "items": items,
                "total": total,
                "skip": skip,
                "limit": limit,
            }
        except Exception as e:
            logger.error(f"Error fetching weight_entries list: {str(e)}")
            raise

    async def update(self, obj_id: int, update_data: Dict[str, Any], user_id: Optional[str] = None) -> Optional[Weight_entries]:
        """Update weight_entries (requires ownership)"""
        try:
            obj = await self.get_by_id(obj_id, user_id=user_id)
            if not obj:
                logger.warning(f"Weight_entries {obj_id} not found for update")
                return None
            for key, value in update_data.items():
                if hasattr(obj, key) and key != 'user_id':
                    setattr(obj, key, value)

            await self.db.commit()
            await self.db.refresh(obj)
            logger.info(f"Updated weight_entries {obj_id}")
            return obj
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating weight_entries {obj_id}: {str(e)}")
            raise

    async def delete(self, obj_id: int, user_id: Optional[str] = None) -> bool:
        """Delete weight_entries (requires ownership)"""
        try:
            obj = await self.get_by_id(obj_id, user_id=user_id)
            if not obj:
                logger.warning(f"Weight_entries {obj_id} not found for deletion")
                return False
            await self.db.delete(obj)
            await self.db.commit()
            logger.info(f"Deleted weight_entries {obj_id}")
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting weight_entries {obj_id}: {str(e)}")
            raise

    async def get_by_field(self, field_name: str, field_value: Any) -> Optional[Weight_entries]:
        """Get weight_entries by any field"""
        try:
            if not hasattr(Weight_entries, field_name):
                raise ValueError(f"Field {field_name} does not exist on Weight_entries")
            result = await self.db.execute(
                select(Weight_entries).where(getattr(Weight_entries, field_name) == field_value)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching weight_entries by {field_name}: {str(e)}")
            raise

    async def list_by_field(
        self, field_name: str, field_value: Any, skip: int = 0, limit: int = 20
    ) -> List[Weight_entries]:
        """Get list of weight_entriess filtered by field"""
        try:
            if not hasattr(Weight_entries, field_name):
                raise ValueError(f"Field {field_name} does not exist on Weight_entries")
            result = await self.db.execute(
                select(Weight_entries)
                .where(getattr(Weight_entries, field_name) == field_value)
                .offset(skip)
                .limit(limit)
                .order_by(Weight_entries.id.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error fetching weight_entriess by {field_name}: {str(e)}")
            raise
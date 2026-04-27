import logging
from typing import Optional, Dict, Any, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.diet_plans import Diet_plans

logger = logging.getLogger(__name__)


# ------------------ Service Layer ------------------
class Diet_plansService:
    """Service layer for Diet_plans operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: Dict[str, Any], user_id: Optional[str] = None) -> Optional[Diet_plans]:
        """Create a new diet_plans"""
        try:
            if user_id:
                data['user_id'] = user_id
            obj = Diet_plans(**data)
            self.db.add(obj)
            await self.db.commit()
            await self.db.refresh(obj)
            logger.info(f"Created diet_plans with id: {obj.id}")
            return obj
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating diet_plans: {str(e)}")
            raise

    async def check_ownership(self, obj_id: int, user_id: str) -> bool:
        """Check if user owns this record"""
        try:
            obj = await self.get_by_id(obj_id, user_id=user_id)
            return obj is not None
        except Exception as e:
            logger.error(f"Error checking ownership for diet_plans {obj_id}: {str(e)}")
            return False

    async def get_by_id(self, obj_id: int, user_id: Optional[str] = None) -> Optional[Diet_plans]:
        """Get diet_plans by ID (user can only see their own records)"""
        try:
            query = select(Diet_plans).where(Diet_plans.id == obj_id)
            if user_id:
                query = query.where(Diet_plans.user_id == user_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching diet_plans {obj_id}: {str(e)}")
            raise

    async def get_list(
        self, 
        skip: int = 0, 
        limit: int = 20, 
        user_id: Optional[str] = None,
        query_dict: Optional[Dict[str, Any]] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get paginated list of diet_planss (user can only see their own records)"""
        try:
            query = select(Diet_plans)
            count_query = select(func.count(Diet_plans.id))
            
            if user_id:
                query = query.where(Diet_plans.user_id == user_id)
                count_query = count_query.where(Diet_plans.user_id == user_id)
            
            if query_dict:
                for field, value in query_dict.items():
                    if hasattr(Diet_plans, field):
                        query = query.where(getattr(Diet_plans, field) == value)
                        count_query = count_query.where(getattr(Diet_plans, field) == value)
            
            count_result = await self.db.execute(count_query)
            total = count_result.scalar()

            if sort:
                if sort.startswith('-'):
                    field_name = sort[1:]
                    if hasattr(Diet_plans, field_name):
                        query = query.order_by(getattr(Diet_plans, field_name).desc())
                else:
                    if hasattr(Diet_plans, sort):
                        query = query.order_by(getattr(Diet_plans, sort))
            else:
                query = query.order_by(Diet_plans.id.desc())

            result = await self.db.execute(query.offset(skip).limit(limit))
            items = result.scalars().all()

            return {
                "items": items,
                "total": total,
                "skip": skip,
                "limit": limit,
            }
        except Exception as e:
            logger.error(f"Error fetching diet_plans list: {str(e)}")
            raise

    async def update(self, obj_id: int, update_data: Dict[str, Any], user_id: Optional[str] = None) -> Optional[Diet_plans]:
        """Update diet_plans (requires ownership)"""
        try:
            obj = await self.get_by_id(obj_id, user_id=user_id)
            if not obj:
                logger.warning(f"Diet_plans {obj_id} not found for update")
                return None
            for key, value in update_data.items():
                if hasattr(obj, key) and key != 'user_id':
                    setattr(obj, key, value)

            await self.db.commit()
            await self.db.refresh(obj)
            logger.info(f"Updated diet_plans {obj_id}")
            return obj
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating diet_plans {obj_id}: {str(e)}")
            raise

    async def delete(self, obj_id: int, user_id: Optional[str] = None) -> bool:
        """Delete diet_plans (requires ownership)"""
        try:
            obj = await self.get_by_id(obj_id, user_id=user_id)
            if not obj:
                logger.warning(f"Diet_plans {obj_id} not found for deletion")
                return False
            await self.db.delete(obj)
            await self.db.commit()
            logger.info(f"Deleted diet_plans {obj_id}")
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting diet_plans {obj_id}: {str(e)}")
            raise

    async def get_by_field(self, field_name: str, field_value: Any) -> Optional[Diet_plans]:
        """Get diet_plans by any field"""
        try:
            if not hasattr(Diet_plans, field_name):
                raise ValueError(f"Field {field_name} does not exist on Diet_plans")
            result = await self.db.execute(
                select(Diet_plans).where(getattr(Diet_plans, field_name) == field_value)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching diet_plans by {field_name}: {str(e)}")
            raise

    async def list_by_field(
        self, field_name: str, field_value: Any, skip: int = 0, limit: int = 20
    ) -> List[Diet_plans]:
        """Get list of diet_planss filtered by field"""
        try:
            if not hasattr(Diet_plans, field_name):
                raise ValueError(f"Field {field_name} does not exist on Diet_plans")
            result = await self.db.execute(
                select(Diet_plans)
                .where(getattr(Diet_plans, field_name) == field_value)
                .offset(skip)
                .limit(limit)
                .order_by(Diet_plans.id.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error fetching diet_planss by {field_name}: {str(e)}")
            raise
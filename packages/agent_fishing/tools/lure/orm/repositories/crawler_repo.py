"""
Crawler Repository for task and log management
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc

from ..repository import BaseRepository
from ...models.system import CrawlerTask, CrawlerLog


class CrawlerRepository(BaseRepository[CrawlerTask]):
    """Repository for Crawler Task management"""

    def __init__(self, session: Session):
        super().__init__(session, CrawlerTask)

    def get_with_logs(self, task_id: int) -> Optional[CrawlerTask]:
        """
        Get crawler task with all logs preloaded

        Args:
            task_id: Task ID

        Returns:
            CrawlerTask instance with preloaded logs or None
        """
        return (
            self.session.query(CrawlerTask)
            .options(joinedload(CrawlerTask.logs))
            .filter(CrawlerTask.id == task_id)
            .first()
        )

    def get_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "id DESC"
    ) -> List[CrawlerTask]:
        """
        Get all crawler tasks with filters

        Args:
            filters: Dictionary of filter conditions
            limit: Maximum number of results
            offset: Pagination offset
            order_by: Field to order by

        Returns:
            List of crawler tasks
        """
        query = self.session.query(CrawlerTask)

        # Apply filters
        if filters:
            if 'task_type' in filters:
                query = query.filter(CrawlerTask.task_type == filters['task_type'])
            if 'status' in filters:
                query = query.filter(CrawlerTask.status == filters['status'])

        # Apply ordering
        if order_by.upper().endswith('DESC'):
            field = order_by.replace(' DESC', '').replace('DESC', '').strip()
            query = query.order_by(desc(getattr(CrawlerTask, field, CrawlerTask.id)))
        else:
            field = order_by.replace(' ASC', '').replace('ASC', '').strip()
            query = query.order_by(getattr(CrawlerTask, field, CrawlerTask.id))

        return query.limit(limit).offset(offset).all()

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count crawler tasks with filters

        Args:
            filters: Dictionary of filter conditions

        Returns:
            Total count
        """
        query = self.session.query(CrawlerTask)

        # Apply filters
        if filters:
            if 'task_type' in filters:
                query = query.filter(CrawlerTask.task_type == filters['task_type'])
            if 'status' in filters:
                query = query.filter(CrawlerTask.status == filters['status'])

        return query.count()

    def get_task_logs(
        self,
        task_id: int,
        level: Optional[str] = None,
        limit: int = 100
    ) -> List[CrawlerLog]:
        """
        Get logs for a specific task

        Args:
            task_id: Task ID
            level: Optional log level filter
            limit: Maximum number of logs

        Returns:
            List of crawler logs
        """
        query = self.session.query(CrawlerLog).filter(CrawlerLog.task_id == task_id)

        if level:
            query = query.filter(CrawlerLog.level == level)

        return query.order_by(CrawlerLog.created_at.asc()).limit(limit).all()

    def update(self, task_id: int, data: Dict[str, Any]) -> Optional[CrawlerTask]:
        """
        Update crawler task

        Args:
            task_id: Task ID
            data: Data to update

        Returns:
            Updated task or None
        """
        task = self.get(task_id)
        if not task:
            return None

        for key, value in data.items():
            if hasattr(task, key):
                setattr(task, key, value)

        self.session.commit()
        self.session.refresh(task)
        return task

    def delete(self, task_id: int) -> bool:
        """
        Delete crawler task (hard delete)

        Args:
            task_id: Task ID

        Returns:
            True if deleted, False if not found
        """
        task = self.get(task_id)
        if not task:
            return False

        self.session.delete(task)
        self.session.commit()
        return True

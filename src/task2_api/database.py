"""
Database operations for task storage and retrieval.
"""

import aiosqlite
import json
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path
from loguru import logger

from .models import TaskStatus


class Database:
    """Async SQLite database for task management."""
    
    def __init__(self, db_path: str = "data/recaptcha.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: Optional[aiosqlite.Connection] = None
    
    async def initialize(self):
        """Initialize database and create tables."""
        self.conn = await aiosqlite.connect(str(self.db_path))
        self.conn.row_factory = aiosqlite.Row
        
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                sitekey TEXT NOT NULL,
                pageurl TEXT NOT NULL,
                proxy TEXT,
                status TEXT NOT NULL,
                token TEXT,
                solve_time REAL,
                error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        await self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_status ON tasks(status)
        """)
        
        await self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at ON tasks(created_at)
        """)
        
        await self.conn.commit()
        logger.info(f"Database initialized at {self.db_path}")
    
    async def create_task(
        self,
        task_id: str,
        sitekey: str,
        pageurl: str,
        proxy: Optional[str],
        status: TaskStatus
    ) -> bool:
        """Create a new task."""
        try:
            now = datetime.now().isoformat()
            await self.conn.execute("""
                INSERT INTO tasks (
                    task_id, sitekey, pageurl, proxy, status,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (task_id, sitekey, pageurl, proxy, status.value, now, now))
            
            await self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return False
    
    async def get_task(self, task_id: str) -> Optional[Dict]:
        """Get task by ID."""
        try:
            cursor = await self.conn.execute(
                "SELECT * FROM tasks WHERE task_id = ?",
                (task_id,)
            )
            row = await cursor.fetchone()
            
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"Error getting task: {e}")
            return None
    
    async def update_task(
        self,
        task_id: str,
        status: TaskStatus,
        token: Optional[str] = None,
        solve_time: Optional[float] = None,
        error: Optional[str] = None
    ) -> bool:
        """Update task status and results."""
        try:
            now = datetime.now().isoformat()
            await self.conn.execute("""
                UPDATE tasks
                SET status = ?, token = ?, solve_time = ?, error = ?, updated_at = ?
                WHERE task_id = ?
            """, (status.value, token, solve_time, error, now, task_id))
            
            await self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating task: {e}")
            return False
    
    async def delete_task(self, task_id: str) -> bool:
        """Delete task by ID."""
        try:
            cursor = await self.conn.execute(
                "DELETE FROM tasks WHERE task_id = ?",
                (task_id,)
            )
            await self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting task: {e}")
            return False
    
    async def get_all_tasks(self, limit: int = 100) -> List[Dict]:
        """Get all tasks with limit."""
        try:
            cursor = await self.conn.execute(
                "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting all tasks: {e}")
            return []
    
    async def get_tasks_by_status(self, status: TaskStatus) -> List[Dict]:
        """Get tasks by status."""
        try:
            cursor = await self.conn.execute(
                "SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC",
                (status.value,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting tasks by status: {e}")
            return []
    
    async def get_statistics(self) -> Dict:
        """Get database statistics."""
        try:
            # Total tasks
            cursor = await self.conn.execute("SELECT COUNT(*) as count FROM tasks")
            row = await cursor.fetchone()
            total = row["count"]
            
            # Tasks by status
            cursor = await self.conn.execute("""
                SELECT status, COUNT(*) as count
                FROM tasks
                GROUP BY status
            """)
            rows = await cursor.fetchall()
            by_status = {row["status"]: row["count"] for row in rows}
            
            # Average solve time
            cursor = await self.conn.execute("""
                SELECT AVG(solve_time) as avg_time
                FROM tasks
                WHERE solve_time IS NOT NULL
            """)
            row = await cursor.fetchone()
            avg_solve_time = row["avg_time"] or 0
            
            # Success rate
            success_count = by_status.get(TaskStatus.READY.value, 0)
            success_rate = (success_count / total * 100) if total > 0 else 0
            
            return {
                "total_tasks": total,
                "by_status": by_status,
                "average_solve_time": round(avg_solve_time, 2),
                "success_rate": round(success_rate, 2)
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    async def cleanup_old_tasks(self, days: int = 7) -> int:
        """Delete tasks older than specified days."""
        try:
            from datetime import timedelta
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            
            cursor = await self.conn.execute(
                "DELETE FROM tasks WHERE created_at < ?",
                (cutoff,)
            )
            await self.conn.commit()
            
            deleted = cursor.rowcount
            logger.info(f"Cleaned up {deleted} old tasks")
            return deleted
        except Exception as e:
            logger.error(f"Error cleaning up tasks: {e}")
            return 0
    
    async def close(self):
        """Close database connection."""
        if self.conn:
            await self.conn.close()
            logger.info("Database connection closed")


# global database instance
_db_instance: Optional[Database] = None

async def get_db() -> Database:
    """Get database instance for dependency injection."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
        # Note: initialize() must be called once at startup
    return _db_instance

async def close_db():
    """Close global database instance."""
    global _db_instance
    if _db_instance is not None:
        await _db_instance.close()
        _db_instance = None

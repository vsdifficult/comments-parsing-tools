from pysondb import db
from typing import Optional, List
from .models import Comment, CreateComment
from logging import getLogger
import json

class CommentsStorage: 
    def __init__(self):
        self._logger = getLogger("CommentsStorage")
        self._storage = db.getDb("comments_db.json")

    async def create_comment(self, CreateComment) -> Optional[bool]:
        try:
            self._storage.add(CreateComment.dict())  
            self._logger.info("Comment created successfully.")
            return True 
        except Exception as e:
            self._logger.error(f"Error creating comment: {e}")
            return False

    async def get_comment(self, comment_id):
        try: 
            comment_data = self._storage.getById(comment_id)
            if comment_data:
                return Comment(**comment_data)
            self._logger.info("Comment not found.")
            return None
        except Exception as e:
            self._logger.error(f"Error retrieving comment: {e}")
            return None

    async def delete_comment(self, comment_id) -> Optional[bool]:
        try:
            self._storage.deleteById(comment_id)
            self._logger.info("Comment deleted successfully.")
            return True
        except Exception as e:
            self._logger.error(f"Error deleting comment: {e}")
            return False

    def save_comments_to_db(self, comments: List[Comment]) -> Optional[bool]:
        """Сохраняет список комментариев в базу данных."""
        try:
            for comment in comments:
                self._storage.add(comment.dict())
            self._logger.info(f"✓ Сохранено {len(comments)} комментариев в базу данных.")
            return True
        except Exception as e:
            self._logger.error(f"Ошибка при сохранении комментариев в БД: {e}")
            return False

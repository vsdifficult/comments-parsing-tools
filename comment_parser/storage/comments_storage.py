from typing import Optional, List
from .models import Comment, CreateComment
from logging import getLogger
import json
import os
import uuid

class CommentsStorage: 
    def __init__(self):
        self._logger = getLogger("CommentsStorage")
        self.db_path = os.path.join(os.path.dirname(__file__), "comments_db.json")
        if not os.path.exists(self.db_path):
            with open(self.db_path, 'w') as f:
                json.dump({}, f)

    def create_comment(self, create_comment_obj) -> Optional[bool]:
        try:
            with open(self.db_path, 'r') as f:
                data = json.load(f)
            comment_id = str(uuid.uuid4())
            data[comment_id] = create_comment_obj.model_dump()
            with open(self.db_path, 'w') as f:
                json.dump(data, f, indent=2)
            self._logger.info("Comment created successfully.")
            return True 
        except Exception as e:
            self._logger.error(f"Error creating comment: {e}")
            return False

    def get_comment(self, comment_id):
        try: 
            with open(self.db_path, 'r') as f:
                data = json.load(f)
            if comment_id in data:
                return Comment(**data[comment_id])
            self._logger.info("Comment not found.")
            return None
        except Exception as e:
            self._logger.error(f"Error retrieving comment: {e}")
            return None

    def get_all_comments(self) -> List[Comment]:
        try:
            with open(self.db_path, 'r') as f:
                data = json.load(f)
            return [Comment(id=k, **v) for k, v in data.items()]
        except Exception as e:
            self._logger.error(f"Error retrieving all comments: {e}")
            return []

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

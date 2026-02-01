import unittest
import os
import json
from comment_parser.storage.comments_storage import CommentsStorage
from comment_parser.storage.models import CreateComment

class TestCommentsStorage(unittest.TestCase):
    def setUp(self):
        self.storage = CommentsStorage()
        if os.path.exists('comments_db.json'):
            os.remove('comments_db.json')

    def test_create_comment(self):
        create_comment = CreateComment(
            url="https://example.com",
            content="Test comment",
            likes=5,
            date="2024-01-01",
            source="test",
            author="TestUser"
        )
        result = self.storage.create_comment(create_comment)
        self.assertTrue(result)

    def test_get_comment(self):
        create_comment = CreateComment(
            url="https://example.com",
            content="Test comment",
            likes=5,
            date="2024-01-01",
            source="test",
            author="TestUser"
        )
        self.storage.create_comment(create_comment)
        
        db_data = self.storage._storage.getAll()
        if db_data:
            comment_id = list(db_data.keys())[0]
            comment = self.storage.get_comment(comment_id)
            self.assertIsNotNone(comment)
            self.assertEqual(comment.content, "Test comment")
        else:
            self.fail("No comments found in database")

    def tearDown(self):
        if os.path.exists('comments_db.json'):
            os.remove('comments_db.json')

if __name__ == '__main__':
    unittest.main()
import unittest
import os
import json
from comment_parser.storage.comments_storage import CommentsStorage
from comment_parser.storage.models import CreateComment

class TestCommentsStorage(unittest.TestCase):
    def setUp(self):
        # Clear any existing file
        db_path = os.path.join(os.path.dirname(__file__), "..", "comment_parser", "storage", "comments_db.json")
        try:
            os.remove(db_path)
        except FileNotFoundError:
            pass
        self.storage = CommentsStorage()

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
        
        all_comments = self.storage.get_all_comments()
        if all_comments:
            comment = all_comments[0]
            self.assertIsNotNone(comment)
            self.assertEqual(comment.content, "Test comment")
        else:
            self.fail("No comments found in database")

    def tearDown(self):
        db_path = os.path.join(os.path.dirname(__file__), "..", "comment_parser", "storage", "comments_db.json")
        try:
            os.remove(db_path)
        except FileNotFoundError:
            pass

if __name__ == '__main__':
    unittest.main()
import unittest
from unittest.mock import patch, MagicMock
from comment_parser.vk.api_vk import ApiVKParser

class TestVKParser(unittest.TestCase):
    def setUp(self):
        self.parser = ApiVKParser()

    @patch('comment_parser.vk.api_vk.requests.get')
    def test_parse_comments_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'response': {
                'items': [
                    {
                        'id': 1,
                        'from_id': 123,
                        'text': 'Test comment',
                        'date': 1640995200,
                        'likes': {'count': 5}
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        result = self.parser.parse_comments('123', 'token', 10, '456')
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

    @patch('comment_parser.vk.api_vk.requests.get')
    def test_parse_comments_api_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'error': {'error_msg': 'Invalid token'}
        }
        mock_get.return_value = mock_response

        result = self.parser.parse_comments('123', 'invalid_token', 10, '456')
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
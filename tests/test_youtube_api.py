import unittest
from unittest.mock import patch, MagicMock
from comment_parser.youtube.api_youtube import YouTubeAPIParser

class TestYouTubeAPIParser(unittest.TestCase):
    def setUp(self):
        self.parser = YouTubeAPIParser()

    @patch('comment_parser.youtube.api_youtube.requests.get')
    def test_parse_comments_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'items': [
                {
                    'snippet': {
                        'topLevelComment': {
                            'snippet': {
                                'textDisplay': 'Test YouTube comment',
                                'authorDisplayName': 'TestUser',
                                'publishedAt': '2024-01-01T00:00:00Z',
                                'likeCount': 10
                            }
                        }
                    }
                }
            ]
        }
        mock_get.return_value = mock_response

        result = self.parser.parse_comments('test_video_id', 'api_key', 10)
        self.assertIsInstance(result, int)
        self.assertGreaterEqual(result, 0)

    @patch('comment_parser.youtube.api_youtube.requests.get')
    def test_parse_comments_api_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'error': {'message': 'Invalid API key'}
        }
        mock_get.return_value = mock_response

        result = self.parser.parse_comments('test_video_id', 'invalid_key', 10)
        self.assertEqual(result, 0)

if __name__ == '__main__':
    unittest.main()
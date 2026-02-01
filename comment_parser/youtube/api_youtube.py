import requests
import json
from typing import List, Optional
from logging import getLogger

from comment_parser.storage.comments_storage import CommentsStorage
from comment_parser.storage.models import CreateComment

class YouTubeAPIParser:
    def __init__(self):
        self._storage = CommentsStorage()
        self._logger = getLogger("YouTubeAPIParser")
        self.base_url = "https://www.googleapis.com/youtube/v3/commentThreads"

    def parse_comments(self, video_id: str, api_key: str, max_comments: int = 100) -> int:
        """
        Parses comments from YouTube video using Data API v3
        
        Args:
            video_id: YouTube video ID
            api_key: YouTube Data API key
            max_comments: Maximum number of comments to retrieve
            
        Returns:
            int: number of saved comments
        """
        saved = 0
        next_page_token = None
        total_fetched = 0
        
        try:
            while total_fetched < max_comments:
                params = {
                    'part': 'snippet',
                    'videoId': video_id,
                    'key': api_key,
                    'maxResults': min(100, max_comments - total_fetched),
                    'order': 'relevance'
                }
                
                if next_page_token:
                    params['pageToken'] = next_page_token
                
                response = requests.get(self.base_url, params=params)
                data = response.json()
                
                if 'error' in data:
                    error_msg = data['error']['message']
                    self._logger.error(f"YouTube API error: {error_msg}")
                    print(f"✗ YouTube API error: {error_msg}")
                    return saved
                
                items = data.get('items', [])
                if not items:
                    break
                
                for item in items:
                    snippet = item['snippet']['topLevelComment']['snippet']
                    
                    comment_text = snippet.get('textDisplay', '')
                    if not comment_text.strip():
                        continue
                    
                    author = snippet.get('authorDisplayName', 'Unknown')
                    published_at = snippet.get('publishedAt', '')
                    like_count = snippet.get('likeCount', 0)
                    
                    url = f"https://www.youtube.com/watch?v={video_id}"
                    
                    create_comment = CreateComment(
                        url=url,
                        content=comment_text,
                        likes=like_count,
                        date=published_at,
                        source="youtube",
                        author=author
                    )
                    
                    if self._storage.create_comment(create_comment):
                        saved += 1
                    
                    total_fetched += 1
                    if total_fetched >= max_comments:
                        break
                
                next_page_token = data.get('nextPageToken')
                if not next_page_token:
                    break
                    
        except Exception as e:
            self._logger.error(f"Failed to parse YouTube comments: {e}")
            print(f"✗ Failed to parse YouTube comments: {e}")
        
        return saved

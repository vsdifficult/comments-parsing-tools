import requests
import json
from typing import Optional, List, Dict
from logging import getLogger
from datetime import datetime

from comment_parser.storage.comments_storage import CommentsStorage
from comment_parser.storage.models import CreateComment

class ApiVKParser: 
    def __init__(self):
        self._storage = CommentsStorage()
        self._logger = getLogger("ApiVKParser")  

    def parse_comments(self, owner_id: str, token: str, count_comms: int, post_id: str) -> Optional[List[Dict]]:
        """
        Parses comments from a VK post
        
        Args:
            owner_id: VK page/group owner ID
            token: VK API access token
            count_comms: Number of comments to retrieve
            post_id: Post ID
            
        Returns:
            List of comment dictionaries or None if error occurs
        """
        try:
            url = 'https://api.vk.com/method/wall.getComments'
            params = {
                'owner_id': owner_id,
                'post_id': post_id,
                'access_token': token,
                'v': '5.131',
                'count': min(count_comms, 100),  
                'extended': 1,  
                'fields': 'first_name,last_name'
            }
            
            print(f"Fetching comments for post {post_id}...")
            response = requests.get(url, params=params)
            data = response.json()
            
            if 'error' in data:
                error_msg = data['error'].get('error_msg', 'Unknown error')
                self._logger.error(f"VK API error: {error_msg}")
                print(f"✗ VK API error: {error_msg}")
                return None
            
            items = data.get('response', {}).get('items', [])
            print(f"✓ Fetched {len(items)} comments")
            return items
            
        except Exception as e:
            self._logger.error(f"Failed to parse comments for post {post_id}: {e}")
            print(f"✗ Failed to parse comments: {e}")
            return None 
        
    def parse_all_comments(self, owner_id: str, token: str, post_id: str, max_comments: Optional[int] = None) -> Optional[List[Dict]]:
        """
        Parses all comments from a VK post using pagination
        
        Args:
            owner_id: VK page/group owner ID
            token: VK API access token
            post_id: Post ID
            max_comments: Maximum number of comments to retrieve (None for all)
            
        Returns:
            List of all comment dictionaries or None if error occurs
        """
        all_comments = []
        offset = 0
        count_per_request = 100  
        
        try:
            while True:
                url = 'https://api.vk.com/method/wall.getComments'
                params = {
                    'owner_id': owner_id,
                    'post_id': post_id,
                    'access_token': token,
                    'v': '5.131',
                    'count': count_per_request,
                    'offset': offset,
                    'extended': 1,
                    'fields': 'first_name,last_name'
                }
                
                print(f"Fetching comments (offset: {offset})...")
                response = requests.get(url, params=params)
                data = response.json()
                
                if 'error' in data:
                    error_msg = data['error'].get('error_msg', 'Unknown error')
                    self._logger.error(f"VK API error: {error_msg}")
                    print(f"✗ VK API error: {error_msg}")
                    return None
                
                items = data.get('response', {}).get('items', [])
                
                if not items:
                    break
                    
                all_comments.extend(items)
                print(f"✓ Collected {len(all_comments)} comments so far")
                
                if max_comments and len(all_comments) >= max_comments:
                    all_comments = all_comments[:max_comments]
                    break
                
                offset += count_per_request
                
            print(f"✓ Total comments collected: {len(all_comments)}")
            return all_comments
            
        except Exception as e:
            self._logger.error(f"Failed to parse all comments for post {post_id}: {e}")
            print(f"✗ Failed to parse comments: {e}")
            return None
    
    def convert_vk_to_create_comment(self, vk_comments: List[Dict], post_url: str) -> List[CreateComment]:
        """
        Converts VK comment format to CreateComment model
        
        Args:
            vk_comments: List of VK API comment dictionaries
            post_url: URL of the VK post
            
        Returns:
            List of CreateComment objects
        """
        create_comments = []
        
        for comment in vk_comments:
            try:
                author = str(comment.get('from_id', 'Unknown'))
                
                timestamp = comment.get('date', 0)
                date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S') if timestamp else ''
                
                create_comment = CreateComment(
                    url=post_url,
                    content=comment.get('text', ''),
                    likes=comment.get('likes', {}).get('count', 0),
                    date=date_str,
                    source="vk",
                    author=author
                )
                create_comments.append(create_comment)
            except Exception as e:
                self._logger.error(f"Failed to convert comment: {e}")
                continue
        
        return create_comments
    
    def save_json(self, owner_id: str, post_id: str, token: str, file_path: str, 
                  max_comments: Optional[int] = None, use_pagination: bool = True) -> int:
        """
        Parses VK comments and saves them to storage
        
        Args:
            owner_id: VK page/group owner ID
            post_id: Post ID
            token: VK API access token
            file_path: Ignored, kept for compatibility
            max_comments: Maximum number of comments to retrieve
            use_pagination: Whether to fetch all comments using pagination
            
        Returns:
            int: number of saved comments
        """
        try:
            print(f"\n{'='*60}")
            print(f"Starting VK comment parsing")
            print(f"Owner ID: {owner_id}, Post ID: {post_id}")
            print(f"{'='*60}\n")
            
            if owner_id.startswith('-'):
                post_url = f"https://vk.com/wall{owner_id}_{post_id}"
            else:
                post_url = f"https://vk.com/wall{owner_id}_{post_id}"
            
            if use_pagination:
                vk_comments = self.parse_all_comments(owner_id, token, post_id, max_comments)
            else:
                count = max_comments if max_comments else 100
                vk_comments = self.parse_comments(owner_id, token, count, post_id)
            
            if vk_comments is None:
                print("✗ Failed to fetch comments")
                return 0
            
            if not vk_comments:
                print("⚠ No comments found")
                return 0
            
            create_comments = self.convert_vk_to_create_comment(vk_comments, post_url)
            
            saved = 0
            for create_comment in create_comments:
                if self._storage.create_comment(create_comment):
                    saved += 1
            
            print(f"\n{'='*60}")
            print(f"✓ Saved {saved} comments to database")
            print(f"{'='*60}\n")
            
            return saved
            
        except Exception as e:
            self._logger.error(f"Failed to save comments to storage: {e}")
            print(f"✗ Failed to save comments: {e}")
            return 0
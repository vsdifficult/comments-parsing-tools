import asyncio
import argparse
import os
import json
import re
from comment_parser.telegram.api_telegram import TelegramCommentsParser
from comment_parser.vk.api_vk import ApiVKParser
from comment_parser.youtube.api_youtube import YouTubeAPIParser
from comment_parser.youtube.selenium_youtube import SeleniumYouTubeParser
from comment_parser.storage.comments_storage import CommentsStorage
from comment_parser.storage.models import CreateComment

def load_config(config_path: str) -> dict:
    """Load configuration from JSON file"""
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load config file {config_path}: {e}")
    return {}

def main():
    parser = argparse.ArgumentParser(description="Comments Parsing Tool")
    parser.add_argument('--platform', choices=['telegram', 'vk', 'youtube'], required=True,
                       help='Platform to parse comments from')
    parser.add_argument('--config', type=str, default='config.json',
                       help='Path to config file with credentials')

    # Telegram specific args
    parser.add_argument('--api_id', type=int, help='Telegram API ID')
    parser.add_argument('--api_hash', type=str, help='Telegram API Hash')
    parser.add_argument('--channel', type=str, help='Telegram channel username')

    # VK specific args
    parser.add_argument('--owner_id', type=str, help='VK owner ID')
    parser.add_argument('--token', type=str, help='VK access token')
    parser.add_argument('--post_id', type=str, help='VK post ID')

    # YouTube specific args
    parser.add_argument('--video_url', type=str, help='YouTube video URL')
    parser.add_argument('--youtube_api_key', type=str, help='YouTube Data API key (optional, uses Selenium if not provided)')

    # Common args
    parser.add_argument('--posts_limit', type=int, default=20, help='Limit for posts (Telegram)')
    parser.add_argument('--comments_limit', type=int, default=200, help='Limit for comments per post')
    parser.add_argument('--max_comments', type=int, help='Maximum comments to parse')

    args = parser.parse_args()

    # Load config
    config = load_config(args.config)
    
    # Override with command line args if provided
    if args.api_id:
        config['telegram_api_id'] = args.api_id
    if args.api_hash:
        config['telegram_api_hash'] = args.api_hash
    if args.token:
        config['vk_token'] = args.token
    if args.youtube_api_key:
        config['youtube_api_key'] = args.youtube_api_key

    try:
        if args.platform == 'telegram':
            api_id = config.get('telegram_api_id')
            api_hash = config.get('telegram_api_hash')
            if not all([api_id, api_hash, args.channel]):
                print("Error: For Telegram, provide --api_id, --api_hash, and --channel or set in config.json")
                return

            async def run_telegram():
                try:
                    parser = TelegramCommentsParser(api_id, api_hash)
                    await parser.connect()
                    saved = await parser.parse_comments(
                        args.channel,
                        posts_limit=args.posts_limit,
                        comments_limit=args.comments_limit
                    )
                    print(f"Saved {saved} comments from Telegram")
                except Exception as e:
                    print(f"Error parsing Telegram comments: {e}")
                finally:
                    try:
                        await parser.disconnect()
                    except:
                        pass

            asyncio.run(run_telegram())

        elif args.platform == 'vk':
            owner_id = args.owner_id
            token = config.get('vk_token')
            if not all([owner_id, token, args.post_id]):
                print("Error: For VK, provide --owner_id, --token, and --post_id or set token in config.json")
                return

            try:
                parser = ApiVKParser()
                saved = parser.save_json(
                    owner_id,
                    args.post_id,
                    token,
                    "",  # file_path not used
                    max_comments=args.max_comments
                )
                if saved > 0:
                    print(f"Saved {saved} comments from VK")
                else:
                    print("Failed to save VK comments")
            except Exception as e:
                print(f"Error parsing VK comments: {e}")

        elif args.platform == 'youtube':
            if not args.video_url:
                print("Error: For YouTube, provide --video_url")
                return

            # Extract video ID from URL
            video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', args.video_url)
            if not video_id_match:
                print("Error: Invalid YouTube URL")
                return
            video_id = video_id_match.group(1)

            api_key = config.get('youtube_api_key') or args.youtube_api_key
            
            try:
                if api_key:
                    # Use API parser
                    parser = YouTubeAPIParser()
                    saved = parser.parse_comments(video_id, api_key, args.max_comments or 100)
                    print(f"Saved {saved} comments from YouTube (API)")
                else:
                    # Use Selenium parser
                    parser = SeleniumYouTubeParser()
                    storage = CommentsStorage()
                    saved = 0
                    for comment in parser.stream_comments(args.video_url, max_comments=args.max_comments):
                        create_comment = CreateComment(
                            url=comment.get('url', args.video_url),
                            content=comment.get('content', ''),
                            likes=comment.get('likes', 0),
                            date=comment.get('date', ''),
                            source='youtube',
                            author=comment.get('author', '')
                        )
                        if storage.create_comment(create_comment):
                            saved += 1
                    print(f"Saved {saved} comments from YouTube (Selenium)")
            except Exception as e:
                print(f"Error parsing YouTube comments: {e}")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()

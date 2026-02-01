# Comments Parsing Tools

A comprehensive Python library for parsing comments from various social media platforms including Telegram, VK (VKontakte), and YouTube. The tool collects comments and stores them in a local JSON database for analysis and processing.

## Features

- **Telegram Comments Parsing**: Extract comments from Telegram channels and discussion groups
- **VK Comments Parsing**: Fetch comments from VK posts with pagination support
- **YouTube Comments Parsing**: Scrape comments from YouTube videos using Selenium
- **Unified Storage**: All parsed comments are stored in a consistent format using PysonDB
- **CLI Interface**: Command-line interface for easy usage
- **Async Support**: Asynchronous operations for efficient parsing

## Installation

1. Clone the repository:
```bash
git clone https://github.com/vsdifficult/comments-parsing-tools.git
cd comments-parsing-tools
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Additional Requirements

For YouTube parsing, you may need to install additional packages:
```bash
pip install undetected-chromedriver selenium
```

For VK parsing, ensure you have a valid VK API token.

## Usage

### Configuration

Create a `config.json` file in the project root to store your API credentials:

```json
{
  "telegram_api_id": 12345678,
  "telegram_api_hash": "your_telegram_api_hash_here",
  "vk_token": "your_vk_access_token_here",
  "youtube_api_key": "your_youtube_data_api_key_here"
}
```

This allows you to avoid passing credentials as command-line arguments each time.

### Command Line Interface

Use the main.py script to parse comments from different platforms:

#### Telegram
```bash
# Using config file
python main.py --platform telegram --channel @channel_username

# Using command line arguments
python main.py --platform telegram --api_id YOUR_API_ID --api_hash YOUR_API_HASH --channel @channel_username --posts_limit 10 --comments_limit 100
```

#### VK
```bash
# Using config file
python main.py --platform vk --owner_id -123456 --post_id 789

# Using command line arguments
python main.py --platform vk --owner_id -123456 --token YOUR_VK_TOKEN --post_id 789 --max_comments 50
```

#### YouTube (API)
```bash
# Using config file
python main.py --platform youtube --video_url "https://www.youtube.com/watch?v=VIDEO_ID"

# Using command line arguments
python main.py --platform youtube --video_url "https://www.youtube.com/watch?v=VIDEO_ID" --youtube_api_key YOUR_API_KEY --max_comments 100
```

#### YouTube (Selenium - fallback)
If no YouTube API key is provided, the tool will use Selenium for web scraping:
```bash
python main.py --platform youtube --video_url "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Programmatic Usage

#### Telegram Parser
```python
import asyncio
from comment_parser.telegram.api_telegram import TelegramCommentsParser

async def main():
    parser = TelegramCommentsParser(api_id=YOUR_API_ID, api_hash="YOUR_API_HASH")
    await parser.connect()
    try:
        saved_count = await parser.parse_comments("@channel_username", posts_limit=5)
        print(f"Saved {saved_count} comments")
    finally:
        await parser.disconnect()

asyncio.run(main())
```

#### VK Parser
```python
from comment_parser.vk.api_vk import ApiVKParser

parser = ApiVKParser()
saved = parser.save_json(
    owner_id="-123456",
    post_id="789",
    token="YOUR_VK_TOKEN",
    file_path="",  # Not used, saves to database
    max_comments=100
)
print(f"Saved {saved} comments")
```

#### YouTube API Parser
```python
from comment_parser.youtube.api_youtube import YouTubeAPIParser

parser = YouTubeAPIParser()
saved = parser.parse_comments("VIDEO_ID", "YOUR_API_KEY", max_comments=50)
print(f"Saved {saved} comments")
```

#### YouTube Selenium Parser
```python
from comment_parser.youtube.selenium_youtube import SeleniumYouTubeParser

parser = SeleniumYouTubeParser()
for comment in parser.stream_comments("https://www.youtube.com/watch?v=VIDEO_ID", max_comments=20):
    print(f"Comment by {comment['author']}: {comment['content']}")
```

## Testing

Run the test suite to verify functionality:

```bash
# Install test dependencies
pip install pytest

# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_storage.py

# Run with verbose output
pytest tests/ -v
```

## Troubleshooting

### Common Issues

#### Telegram
- **"Client not connected"**: Ensure your API credentials are correct and you have internet connection
- **"Channel not found"**: Check the channel username format (@username)
- **Rate limiting**: Add delays between requests if needed

#### VK
- **"Invalid token"**: Regenerate your VK access token
- **"Access denied"**: Ensure your token has the necessary permissions
- **Empty results**: Check owner_id format (negative for groups)

#### YouTube
- **API quota exceeded**: YouTube Data API has daily limits. Consider using Selenium fallback
- **Comments disabled**: Some videos don't allow comments
- **Selenium issues**: Ensure Chrome browser is installed and up-to-date

#### General
- **Import errors**: Run `pip install -r requirements.txt`
- **Database issues**: Check write permissions for `comments_db.json`
- **Network timeouts**: Check your internet connection

### Debug Mode

For YouTube Selenium parsing, you can enable debug output:
```python
parser = SeleniumYouTubeParser()
for comment in parser.stream_comments(video_url, debug=True):
    # Debug information will be printed
    pass
```

### Logs

Check the console output for detailed error messages and progress information. All parsers include logging for troubleshooting.

## Advanced Usage

### Custom Storage

You can extend the `CommentsStorage` class for custom storage backends:

```python
from comment_parser.storage.comments_storage import CommentsStorage

class CustomStorage(CommentsStorage):
    def save_to_custom_db(self, comments):
        # Your custom logic here
        pass
```

### Batch Processing

For processing multiple sources:

```python
sources = [
    {"platform": "telegram", "channel": "@channel1"},
    {"platform": "vk", "owner_id": "-123", "post_id": "456"},
    {"platform": "youtube", "video_url": "https://youtube.com/watch?v=789"}
]

for source in sources:
    # Run parsing for each source
    pass
```

## Advanced Usage

### Custom Storage

You can extend the `CommentsStorage` class for custom storage backends:

```python
from comment_parser.storage.comments_storage import CommentsStorage

class CustomStorage(CommentsStorage):
    def save_to_custom_db(self, comments):
        # Your custom logic here
        pass
```

### Batch Processing

For processing multiple sources:

```python
sources = [
    {"platform": "telegram", "channel": "@channel1"},
    {"platform": "vk", "owner_id": "-123", "post_id": "456"},
    {"platform": "youtube", "video_url": "https://youtube.com/watch?v=789"}
]

for source in sources:
    # Run parsing for each source
    pass
```

## Configuration

### Telegram
- Obtain API credentials from https://my.telegram.org/
- `api_id`: Your Telegram API ID
- `api_hash`: Your Telegram API Hash

### VK
- Create a VK application at https://vk.com/dev
- Get an access token with appropriate permissions
- `owner_id`: Group or user ID (negative for groups)
- `token`: VK API access token

### YouTube
- No API key required (uses Selenium web scraping)
- Ensure Chrome browser is installed
- `video_url`: Full YouTube video URL

## Storage

Comments are stored in `comment_parser/storage/comments_db.json` using PysonDB.

Each comment record contains:
- `id`: Unique identifier
- `url`: Source URL
- `content`: Comment text
- `likes`: Number of likes/reactions
- `date`: Comment date
- `source`: Platform (telegram/vk/youtube)
- `author`: Comment author

## Dependencies

- `telethon`: Telegram API client
- `requests`: HTTP requests for VK API
- `selenium`: Web scraping for YouTube
- `pysondb`: JSON database storage
- `pydantic`: Data validation
- `undetected-chromedriver`: Anti-detection Chrome driver (optional)

## Project Structure

```
comments-parsing-tools/
├── main.py                          # CLI entry point
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
└── comment_parser/
    ├── storage/
    │   ├── __init__.py
    │   ├── comments_db.json         # Comments database
    │   ├── comments_storage.py      # Storage interface
    │   └── models.py                # Data models
    ├── telegram/
    │   ├── __init__.py
    │   ├── api_telegram.py          # Telegram parser
    │   └── utils/
    ├── vk/
    │   ├── __init__.py
    │   ├── api_vk.py                # VK parser
    │   └── utils/
    └── youtube/
        ├── __init__.py
        ├── api_youtube.py           # YouTube API parser (empty)
        ├── selenium_youtube.py      # YouTube Selenium parser
        └── utils/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational and research purposes only. Respect the terms of service of the platforms you scrape and ensure you have permission to collect data. Rate limiting and responsible usage is recommended to avoid being blocked.
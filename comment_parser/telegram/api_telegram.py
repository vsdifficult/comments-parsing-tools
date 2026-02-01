
import asyncio
from typing import List, Dict, Optional

from telethon import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import Message

from ..storage.comments_storage import CommentsStorage
from ..storage.models import CreateComment


class TelegramCommentsParser:
    def __init__(
        self,
        api_id: int,
        api_hash: str,
        session_name: str = "comments_parser"
    ):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.client: Optional[TelegramClient] = None
        self.storage = CommentsStorage()

    async def connect(self):
        self.client = TelegramClient(
            self.session_name,
            self.api_id,
            self.api_hash
        )
        await self.client.start()

    async def disconnect(self):
        if self.client:
            await self.client.disconnect()

    async def parse_comments(
        self,
        channel_username: str,
        posts_limit: int = 20,
        comments_limit: int = 200,
        sleep: float = 1.0
    ) -> int:

        if not self.client:
            raise RuntimeError("Client not connected")

        channel = await self.client.get_entity(channel_username)

        full = await self.client(GetFullChannelRequest(channel))
        linked_chat_id = full.full_chat.linked_chat_id

        if not linked_chat_id:
            return 0

        discussion = await self.client.get_entity(linked_chat_id)

        post_ids = []
        async for msg in self.client.iter_messages(channel, limit=posts_limit):
            if msg.id:
                post_ids.append(msg.id)

        saved_count = 0

        for post_id in post_ids:
            async for comment in self.client.iter_messages(
                discussion,
                reply_to=post_id,
                limit=comments_limit
            ):
                if isinstance(comment, Message) and comment.text:
                    author = "unknown"
                    if comment.from_id:
                        try:
                            user = await self.client.get_entity(comment.from_id)
                            author = user.username or f"{user.first_name or ''} {user.last_name or ''}".strip() or str(comment.from_id.user_id)
                        except:
                            author = str(comment.from_id.user_id)

                    url = f"https://t.me/{channel_username}/{post_id}?comment={comment.id}"
                    create_comment = CreateComment(
                        url=url,
                        content=comment.text,
                        likes=0,  
                        date=comment.date.isoformat() if comment.date else "",
                        source="telegram",
                        author=author
                    )
                    success = await self.storage.create_comment(create_comment)
                    if success:
                        saved_count += 1

            await asyncio.sleep(sleep)

        return saved_count

import os
import aiohttp
import asyncio
import urllib.parse
import json
from typing import Dict, Any, List, Optional

DISCORD_BOT_TOKEN = os.getenv("DN_DISCORD_BOT_TOKEN", "")
BASE_URL = os.getenv("APP_BASE_URL", "https://dn.koharu.live")

# Channels Mapping
DEV_CHAT_CHANNELS = {
    "ko": 1560896208980025468,  # 💻┃한국어개발
    "en": 1560896229188313208,  # 💻┃devchaten
    "ja": 1560896247102050374   # 💻┃日本語開発
}

QNA_FORUM_CHANNELS = {
    "ko": 1560895939315769384,  # 💡┃한국어qna
    "en": 1560895970907000852,  # 💡┃devqna
    "ja": 1560895987453657098   # 💡┃開発質問qna
}

# --- Translation Utility ---
async def translate_text(text: str, target_lang: str) -> str:
    """Translates text into target_lang ('en', 'ko', 'ja') using Google's fast engine."""
    if not text or not text.strip():
        return ""
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q=" + urllib.parse.quote(text)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=aiohttp.ClientTimeout(total=4)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return "".join([item[0] for item in data[0] if item[0]])
    except Exception as e:
        print(f"Translation error to {target_lang}: {e}")
    return text

async def generate_multilang_summaries(title: str, content: str) -> Dict[str, Dict[str, str]]:
    """Generates localized title and summary for ko, en, and ja."""
    summary_src = content[:400] + ("..." if len(content) > 400 else "")
    
    # Run translations concurrently
    tasks = [
        translate_text(title, "ko"),
        translate_text(summary_src, "ko"),
        translate_text(title, "en"),
        translate_text(summary_src, "en"),
        translate_text(title, "ja"),
        translate_text(summary_src, "ja"),
    ]
    results = await asyncio.gather(*tasks)
    
    return {
        "ko": {"title": results[0], "summary": results[1]},
        "en": {"title": results[2], "summary": results[3]},
        "ja": {"title": results[4], "summary": results[5]},
    }


# --- Discord REST Helpers ---
def get_discord_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "DevNetworkBot (https://dn-web-mocha.vercel.app, 1.0)"
    }

async def discord_create_article_thread(lang: str, title: str, summary: str, article_id: int, image_url: Optional[str] = None) -> Optional[Dict[str, str]]:
    """Creates a public thread in the language's dev-chat channel with Components V2 link card."""
    channel_id = DEV_CHAT_CHANNELS.get(lang)
    if not channel_id or not DISCORD_BOT_TOKEN:
        return None
    
    thread_name = f"[{lang.upper()}] {title[:90]}"
    article_url = f"{BASE_URL}/article/{article_id}"
    headers = get_discord_headers()
    
    try:
        async with aiohttp.ClientSession() as session:
            # 1. Create Public Thread
            create_url = f"https://discord.com/api/v10/channels/{channel_id}/threads"
            payload = {
                "name": thread_name,
                "auto_archive_duration": 1440,
                "type": 11 # PUBLIC_THREAD
            }
            async with session.post(create_url, headers=headers, json=payload) as resp:
                if resp.status not in (200, 201):
                    err_text = await resp.text()
                    print(f"Failed to create thread in {channel_id}: {resp.status} {err_text}")
                    return None
                thread_data = await resp.json()
                thread_id = thread_data["id"]

            # 2. Post Initial Message with Components V2 Link Card and Separator
            msg_url = f"https://discord.com/api/v10/channels/{thread_id}/messages"
            button_label = {
                "ko": "웹에서 전체 글 읽기",
                "en": "Read Full Article on Web",
                "ja": "ウェブで全文を読む"
            }.get(lang, "Read Full Article")
            
            sep = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            thin = "────────────────────────────────────"
            summary_clean = "\n> ".join(summary.split("\n"))
            content_text = (
                f">>> 📰 **{title}** ⁝ `TECH NEWS`\n"
                f"> {sep}\n"
                f"> {summary_clean}\n"
                f"> {thin}\n"
                f"> ▫️ **공유 링크**: {article_url}"
            )
            
            # Components V2 Payload (Button + Action Row)
            v2_components = [
                {
                    "type": 1, # ACTION_ROW
                    "components": [
                        {
                            "type": 2, # BUTTON
                            "style": 5, # LINK
                            "label": button_label,
                            "url": article_url
                        }
                    ]
                }
            ]

            msg_payload = {
                "content": content_text,
                "components": v2_components
            }
            if image_url and not image_url.startswith("data:"):
                msg_payload["embeds"] = [{
                    "image": {"url": image_url},
                    "color": 3907797
                }]
            
            async with session.post(msg_url, headers=headers, json=msg_payload) as msg_resp:
                msg_id = ""
                if msg_resp.status in (200, 201):
                    msg_data = await msg_resp.json()
                    msg_id = msg_data.get("id", "")
                else:
                    err_text = await msg_resp.text()
                    print(f"Message send error: {msg_resp.status} {err_text}")
                
                return {
                    "lang": lang,
                    "channel_id": str(channel_id),
                    "thread_id": str(thread_id),
                    "message_id": str(msg_id)
                }
    except Exception as e:
        print(f"Error in discord_create_article_thread: {e}")
        return None

async def discord_create_forum_post(lang: str, title: str, content: str, post_id: int, image_url: Optional[str] = None) -> Optional[str]:
    """Creates a forum post in the dedicated Q&A forum channel with Components V2 link card."""
    forum_id = QNA_FORUM_CHANNELS.get(lang)
    if not forum_id or not DISCORD_BOT_TOKEN:
        return None
    
    qna_url = f"{BASE_URL}/qna/{post_id}"
    headers = get_discord_headers()
    
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://discord.com/api/v10/channels/{forum_id}/threads"
            button_label = {
                "ko": "DevNetwork Q&A 포럼에서 보기",
                "en": "View on DevNetwork Q&A",
                "ja": "DevNetwork Q&Aで確認"
            }.get(lang, "View on Q&A")
            
            sep = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            thin = "────────────────────────────────────"
            content_clean = "\n> ".join(content[:1200].split("\n"))
            container_text = (
                f">>> 💡 **{title}** ⁝ `Q&A FORUM`\n"
                f"> {sep}\n"
                f"> {content_clean}\n"
                f"> {thin}\n"
                f"> ▫️ **포럼 동기화 링크**: {qna_url}"
            )

            msg_obj = {
                "content": container_text,
                "components": [
                    {
                        "type": 1,
                        "components": [
                            {
                                "type": 2,
                                "style": 5,
                                "label": button_label,
                                "url": qna_url
                            }
                        ]
                    }
                ]
            }
            if image_url and not image_url.startswith("data:"):
                msg_obj["embeds"] = [{
                    "image": {"url": image_url},
                    "color": 3907797
                }]
                
            payload = {
                "name": title[:99],
                "auto_archive_duration": 4320,
                "message": msg_obj
            }
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status in (200, 201):
                    data = await resp.json()
                    return str(data["id"])
                else:
                    err = await resp.text()
                    print(f"Failed to create forum post: {resp.status} {err}")
    except Exception as e:
        print(f"Error creating forum post: {e}")
    return None

async def discord_send_thread_message(thread_id: str, author_name: str, content: str) -> Optional[str]:
    """Sends an answer message to an existing Discord thread."""
    if not thread_id or not DISCORD_BOT_TOKEN:
        return None
    
    headers = get_discord_headers()
    url = f"https://discord.com/api/v10/channels/{thread_id}/messages"
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "content": f"💬 **{author_name}** (from Web Portal):\n{content}"
            }
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status in (200, 201):
                    data = await resp.json()
                    return str(data.get("id"))
    except Exception as e:
        print(f"Error sending thread message: {e}")
    return None

async def discord_fetch_forum_threads(forum_id: int) -> List[Dict[str, Any]]:
    """Fetches active and recently archived threads from a Discord forum channel."""
    if not DISCORD_BOT_TOKEN:
        return []
    
    headers = get_discord_headers()
    threads = []
    try:
        async with aiohttp.ClientSession() as session:
            # Active threads
            url = f"https://discord.com/api/v10/channels/{forum_id}/threads/active"
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    threads.extend(data.get("threads", []))
                    
            # Archived threads
            url_arch = f"https://discord.com/api/v10/channels/{forum_id}/threads/archived/public?limit=25"
            async with session.get(url_arch, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    threads.extend(data.get("threads", []))
    except Exception as e:
        print(f"Error fetching forum threads: {e}")
    return threads

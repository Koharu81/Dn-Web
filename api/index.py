import os
import aiohttp
import asyncpg
import markdown
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Request, Response, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .db import (
    db_get_articles, db_get_article, db_create_article, db_save_article_thread,
    db_get_article_threads, db_toggle_upvote, db_get_article_comments, db_add_article_comment,
    db_get_qna_posts, db_get_qna_post, db_create_qna_post, db_update_qna_discord_thread,
    db_get_qna_answers, db_add_qna_answer, db_upsert_discord_forum_thread
)
from .discord_sync import (
    generate_multilang_summaries, discord_create_article_thread,
    discord_create_forum_post, discord_send_thread_message, discord_fetch_forum_threads,
    DEV_CHAT_CHANNELS, QNA_FORUM_CHANNELS
)

app = FastAPI(title="DevNetwork Global Tech Hub")

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)

DISCORD_BOT_TOKEN = os.getenv("DN_DISCORD_BOT_TOKEN", "")
DISCORD_CLIENT_ID = os.getenv("DN_CLIENT_ID", "")
DISCORD_CLIENT_SECRET = os.getenv("DN_CLIENT_SECRET", "")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://neondb_owner:npg_Zla3NzLDfK6M@ep-odd-lake-b58efh05-pooler.c-7.us-east-2.aws.neon.tech/neondb?sslmode=require")
APP_BASE_URL = os.getenv("APP_BASE_URL", "https://dn.koharu.live")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "https://dn.koharu.live/auth/discord/callback")

GUILD_ID = 1552469048099471390
ROLE_IDS = {
    "ko": 1555128535989882910, # 한국어
    "en": 1555128570634829884, # English
    "ja": 1555128606513168447  # 日本語
}

# --- Translations (Zero Emojis, Pure Tech Editorial Style) ---
TRANSLATIONS = {
    "en": {
        "nav_articles": "Articles",
        "nav_qna": "Q&A Forum",
        "nav_submit": "Submit Post",
        "login_discord": "Login with Discord",
        "logout": "Logout",
        "feed_tab_latest": "Latest",
        "feed_tab_popular": "Popular",
        "all_languages": "All Languages",
        "filter_tag": "Filter by Tag",
        "switch_role_lang": "Change Language Role",
        "modal_title": "Select Primary Community Language",
        "modal_desc": "Choose your primary language for the DevNetwork community. Your Discord server role will be updated instantly.",
        "close": "Close",
        "empty_feed": "No articles published yet. Be the first to share engineering insights!",
        "post_threads_linked": "Discord Dev-Chat Threads Synchronized",
        "read_article": "Read Article",
        "comments": "Comments",
        "add_comment": "Post Comment",
        "comment_placeholder": "Share constructive feedback or technical questions...",
        "submit_article_title": "Submit Engineering Article / Tech News",
        "submit_article_desc": "Articles are automatically translated into English, Korean, and Japanese, with interactive threads created in Discord developer channels.",
        "input_title": "Title",
        "input_external_url": "External URL (Optional, for GeekNews style curation)",
        "input_tags": "Tags (comma separated, e.g., python, devops, ai)",
        "input_content": "Content (Markdown supported)",
        "input_image_url": "Banner / Diagram Image URL (Optional)",
        "btn_publish": "Publish & Broadcast to Discord",
        "qna_title": "Community Q&A Forum",
        "qna_desc": "Two-way synchronized developer forum connecting Web Portal and Discord Language Forums.",
        "ask_question": "Ask Question",
        "qna_all": "All",
        "qna_open": "Open",
        "qna_solved": "Solved",
        "qna_empty": "No questions found in this category.",
        "answers": "Answers",
        "your_answer": "Your Answer",
        "submit_answer": "Post Answer to Discord & Web",
        "view_in_discord": "View in Discord Forum",
        "sync_discord": "Sync from Discord Forums",
        "landing_pill": "Global Engineering Community & Dev Hub",
        "landing_hero_title": "Enterprise Engineering Hub\nfor Global Developers",
        "landing_hero_desc": "Connecting developers across English, Korean, and Japanese with real-time translation, GeekNews style articles, and Discord forum synchronization.",
        "landing_cta": "Login with Discord to Access Community",
        "landing_preview_articles": "Latest Engineering Articles",
        "landing_preview_qna": "Live Community Q&A",
        "landing_login_to_view": "Discord login is required to read full articles and participate in discussions.",
        "section_infrastructure": "Core Community Infrastructure",
        "section_infrastructure_desc": "Next-gen Discord Components V2 Architecture & Global Developer Feed",
        "pillar_geeknews_title": "GeekNews Tech Feed",
        "pillar_geeknews_desc": "Curated engineering insights, architecture updates, and tech news with Markdown support and community upvotes.",
        "pillar_v2_title": "Discord Components V2",
        "pillar_v2_desc": "Articles are automatically translated and summarized across EN, KO, and JA with interactive V2 link cards in dev-chat.",
        "pillar_sync_title": "Real-time Forum Sync",
        "pillar_sync_desc": "Two-way synchronization between the web Q&A portal and Discord 3-language forum channels.",
        "login_to_view": "Login to View",
        "by_author": "By",
        "no_articles_yet": "No articles published yet.",
        "no_questions_yet": "No questions posted yet.",
        "back_to_articles": "Back to Articles",
        "back_to_qna": "Back to Q&A Forum",
        "source_link": "Source Link",
        "discord_thread_title": "Discord Dev-Chat Threads (Components V2 Broadcasted)",
        "discord_thread_ko": "Korean Dev-Chat Thread",
        "discord_thread_en": "English Dev-Chat Thread",
        "discord_thread_ja": "Japanese Dev-Chat Thread",
        "no_comments_yet": "No comments yet.",
        "login_to_comment": "Login with Discord to join technical discussions",
        "write_notice_title": "Discord Thread Auto-Routing:",
        "write_notice_desc": "Publishing this post will create dedicated public threads across the Korean, English, and Japanese dev-chat channels using official Discord Components V2 link embeds.",
        "input_title_placeholder": "e.g., Designing Microservices with Async Python and PostgreSQL",
        "input_tags_placeholder": "python, postgresql, system-design",
        "input_content_placeholder": "Write engineering insights in Markdown...",
        "cancel": "Cancel",
        "qna_new_desc": "Post engineering questions that sync instantly to Discord language forum channels.",
        "qna_new_notice_title": "Real-time Forum Sync:",
        "qna_new_notice_desc": "Selecting your language will automatically create a forum thread in Discord's dedicated forum channel.",
        "target_forum_label": "Target Language Forum *",
        "target_forum_ko": "Korean Developer Q&A Forum",
        "target_forum_en": "English Developer Q&A Forum",
        "target_forum_ja": "Japanese Developer Q&A Forum",
        "qna_input_title_placeholder": "e.g., How to handle race conditions in async PostgreSQL pool?",
        "qna_input_content_placeholder": "Detail the technical issue, error logs, and expected behavior...",
        "qna_submit_btn": "Submit to Web & Discord",
        "live_in_discord": "This question is live in Discord Forum",
        "no_answers_yet": "No answers posted yet.",
        "answer_placeholder": "Provide a helpful technical answer (will sync to Discord)...",
        "login_to_answer": "Login with Discord to answer this question",
        "discord_forum_synced": "Discord Forum Synced",
        "footer_text": "© 2026 DevNetwork. Enterprise Discord & GitHub Automation Architecture."
    },
    "ko": {
        "nav_articles": "아티클 / 테크뉴스",
        "nav_qna": "Q&A 포럼",
        "nav_submit": "글 작성",
        "login_discord": "디스코드 로그인",
        "logout": "로그아웃",
        "feed_tab_latest": "최신순",
        "feed_tab_popular": "인기순",
        "all_languages": "전체 언어",
        "filter_tag": "태그 필터",
        "switch_role_lang": "메인 언어 역할 변경",
        "modal_title": "메인 언어 역할을 선택해주세요",
        "modal_desc": "DevNetwork 커뮤니티에서 활동하실 주 언어를 선택하시면 디스코드 서버 역할이 자동으로 동기화됩니다.",
        "close": "닫기",
        "empty_feed": "등록된 아티클이 없습니다. 첫 엔지니어링 지식을 공유해보세요!",
        "post_threads_linked": "디스코드 데브챗 3개 국어 스레드 연동 완료",
        "read_article": "전문 읽기",
        "comments": "댓글",
        "add_comment": "댓글 작성",
        "comment_placeholder": "건설적인 피드백이나 질문을 남겨주세요...",
        "submit_article_title": "엔지니어링 아티클 / 테크 뉴스 작성",
        "submit_article_desc": "작성하신 글은 한국어, 영어, 일본어로 실시간 번역 요약되어 각 언어 카테고리의 데브 챗 채널에 전용 스레드로 자동 발행됩니다.",
        "input_title": "제목",
        "input_external_url": "외부 링크 (선택사항, 긱뉴스 형태 공유)",
        "input_tags": "태그 (쉼표로 구분, 예: python, devops, ai)",
        "input_content": "본문 내용 (마크다운 지원)",
        "input_image_url": "대표 이미지 / 다이어그램 URL (선택사항)",
        "btn_publish": "발행 및 디스코드 동기화",
        "qna_title": "개발자 Q&A 포럼",
        "qna_desc": "웹 포털과 디스코드 언어별 포럼 채널이 실시간 양방향으로 동기화되는 커뮤니티 공간입니다.",
        "ask_question": "질문하기",
        "qna_all": "전체",
        "qna_open": "미해결",
        "qna_solved": "해결됨",
        "qna_empty": "해당 카테고리에 질문이 없습니다.",
        "answers": "답변",
        "your_answer": "답변 작성하기",
        "submit_answer": "답변 등록 (웹 및 디스코드 동시 전송)",
        "view_in_discord": "디스코드 포럼에서 확인",
        "sync_discord": "디스코드 포럼 동기화",
        "landing_pill": "글로벌 IT 커뮤니티 & 엔지니어링 허브",
        "landing_hero_title": "개발자를 위한\n글로벌 엔지니어링 네트워크",
        "landing_hero_desc": "한국어, 영어, 일본어 3개 언어로 실시간 상호 연결되는 테크 아티클과 Q&A 포럼. 디스코드로 로그인하여 글로벌 개발자 커뮤니티에 참여하세요.",
        "landing_cta": "디스코드로 로그인하여 시작하기",
        "landing_preview_articles": "최신 테크 아티클",
        "landing_preview_qna": "실시간 커뮤니티 Q&A",
        "landing_login_to_view": "전체 글 열람 및 커뮤니티 참여는 디스코드 로그인이 필요합니다.",
        "section_infrastructure": "핵심 커뮤니티 인프라",
        "section_infrastructure_desc": "차세대 디스코드 컴포넌트 아키텍처와 글로벌 개발자 피드",
        "pillar_geeknews_title": "긱뉴스 테크 피드",
        "pillar_geeknews_desc": "최신 개발 지식과 기술 뉴스를 마크다운 및 추천(Upvote) 시스템으로 공유하는 테크 아티클 플랫폼입니다.",
        "pillar_v2_title": "디스코드 컴포넌트 V2",
        "pillar_v2_desc": "글 작성 시 한국어, 영어, 일본어로 즉시 번역 요약되어 각 언어 개발 채널에 V2 링크 카드로 스레드가 자동 생성됩니다.",
        "pillar_sync_title": "실시간 포럼 양방향 동기화",
        "pillar_sync_desc": "웹 포털의 Q&A 질문/답변과 디스코드 서버 내의 3개 국어 포럼 채널이 실시간 양방향으로 동기화됩니다.",
        "login_to_view": "로그인 후 확인",
        "by_author": "작성자:",
        "no_articles_yet": "아직 등록된 아티클이 없습니다.",
        "no_questions_yet": "아직 등록된 질문이 없습니다.",
        "back_to_articles": "아티클 목록으로",
        "back_to_qna": "Q&A 포럼으로",
        "source_link": "원문 링크",
        "discord_thread_title": "디스코드 데브챗 스레드 (컴포넌트 V2 연동)",
        "discord_thread_ko": "한국어 데브챗 스레드",
        "discord_thread_en": "영어 데브챗 스레드",
        "discord_thread_ja": "일본어 데브챗 스레드",
        "no_comments_yet": "아직 작성된 댓글이 없습니다.",
        "login_to_comment": "기술 토론에 참여하려면 디스코드로 로그인하세요",
        "write_notice_title": "디스코드 스레드 자동 라우팅:",
        "write_notice_desc": "글을 발행하면 한국어, 영어, 일본어 데브챗 채널에 공식 디스코드 컴포넌트 V2 링크 임베드가 포함된 전용 스레드가 자동 생성됩니다.",
        "input_title_placeholder": "예: 비동기 Python과 PostgreSQL로 마이크로서비스 설계하기",
        "input_tags_placeholder": "python, postgresql, system-design",
        "input_content_placeholder": "마크다운 형식으로 엔지니어링 지식을 공유해주세요...",
        "cancel": "취소",
        "qna_new_desc": "디스코드의 각 언어별 포럼 채널로 즉시 동기화되는 개발 질문을 등록하세요.",
        "qna_new_notice_title": "실시간 포럼 동기화:",
        "qna_new_notice_desc": "질문 언어를 선택하면 해당 언어의 디스코드 전용 포럼 채널에 스레드가 자동으로 생성됩니다.",
        "target_forum_label": "연동 포럼 언어 선택 *",
        "target_forum_ko": "한국어 개발 Q&A 포럼",
        "target_forum_en": "영어 개발 Q&A 포럼",
        "target_forum_ja": "일본어 개발 Q&A 포럼",
        "qna_input_title_placeholder": "예: 비동기 PostgreSQL 커넥션 풀의 경쟁 상태를 방지하는 방법은?",
        "qna_input_content_placeholder": "발생한 문제 상황, 에러 로그, 기대 동작 등을 자세히 작성해주세요...",
        "qna_submit_btn": "웹 및 디스코드에 동시 등록",
        "live_in_discord": "이 질문은 디스코드 포럼 채널과 실시간 연동되어 있습니다",
        "no_answers_yet": "아직 작성된 답변이 없습니다.",
        "answer_placeholder": "도움이 되는 기술 답변을 남겨주세요 (디스코드 포럼에 자동 동기화됩니다)...",
        "login_to_answer": "답변을 작성하려면 디스코드로 로그인하세요",
        "discord_forum_synced": "디스코드 포럼 동기화됨",
        "footer_text": "© 2026 DevNetwork. 엔터프라이즈 디스코드 & 깃허브 자동화 아키텍처."
    },
    "ja": {
        "nav_articles": "記事・テックニュース",
        "nav_qna": "Q&Aフォーラム",
        "nav_submit": "投稿する",
        "login_discord": "Discordでログイン",
        "logout": "ログアウト",
        "feed_tab_latest": "最新順",
        "feed_tab_popular": "人気順",
        "all_languages": "すべての言語",
        "filter_tag": "タグで絞り込み",
        "switch_role_lang": "メイン言語ロールを変更",
        "modal_title": "メイン言語ロールを選択してください",
        "modal_desc": "DevNetworkコミュニティで利用する言語を選択すると、Discordのロールが即座に同期されます。",
        "close": "閉じる",
        "empty_feed": "まだ記事が投稿されていません。最初の技術知見を共有しましょう！",
        "post_threads_linked": "Discord開発チャンネルに3言語スレッド連携完了",
        "read_article": "記事を読む",
        "comments": "コメント",
        "add_comment": "コメントを投稿",
        "comment_placeholder": "建設的なフィードバックや質問を入力してください...",
        "submit_article_title": "技術記事・テックニュースの投稿",
        "submit_article_desc": "投稿された内容は英語・韓国語・日本語に自動要約翻訳され、Discordの各言語開発チャンネルにスレッドとして自動配信されます。",
        "input_title": "タイトル",
        "input_external_url": "外部リンク（任意、GeekNews形式のキュレーション）",
        "input_tags": "タグ（カンマ区切り、例: python, devops, ai）",
        "input_content": "本文（Markdown対応）",
        "input_image_url": "アイキャッチ画像 / 図解URL（任意）",
        "btn_publish": "公開してDiscordに配信",
        "qna_title": "エンジニア Q&A フォーラム",
        "qna_desc": "WebポータルとDiscordの各言語フォーラムがリアルタイム双方向同期するコミュニティです。",
        "ask_question": "質問する",
        "qna_all": "すべて",
        "qna_open": "未解決",
        "qna_solved": "解決済み",
        "qna_empty": "該当する質問は見つかりませんでした。",
        "answers": "回答",
        "your_answer": "回答を投稿",
        "submit_answer": "回答を送信（WebおよびDiscordに反映）",
        "view_in_discord": "Discordフォーラムで確認",
        "sync_discord": "Discordフォーラムと同期",
        "landing_pill": "グローバルITコミュニティ＆開発ハブ",
        "landing_hero_title": "エンジニアのための\nグローバル技術ネットワーク",
        "landing_hero_desc": "英語、韓国語、日本語の3言語でリアルタイム相互接続する技術記事とQ&Aフォーラム。Discordでログインしてコミュニティに参加しましょう。",
        "landing_cta": "Discordでログインして開始",
        "landing_preview_articles": "最新の技術記事",
        "landing_preview_qna": "リアルタイム Q&A",
        "landing_login_to_view": "記事の全文閲覧や投稿にはDiscordログインが必要です。",
        "section_infrastructure": "コアコミュニティインフラ",
        "section_infrastructure_desc": "次世代Discordコンポーネントアーキテクチャとグローバル開発者フィード",
        "pillar_geeknews_title": "GeekNews 技術フィード",
        "pillar_geeknews_desc": "最新の開発知見や技術ニュースをマークダウン記法とUpvoteシステムで共有する技術記事プラットフォームです。",
        "pillar_v2_title": "Discord コンポーネント V2",
        "pillar_v2_desc": "投稿時に英語、韓国語、日本語へ即座に要約翻訳され、各言語の開発チャンネルにV2リンクカードとしてスレッドが自動生成されます。",
        "pillar_sync_title": "リアルタイムフォーラム双方向同期",
        "pillar_sync_desc": "WebポータルのQ&A質問・回答とDiscordサーバー内の3言語フォーラムチャンネルがリアルタイムで双方向同期されます。",
        "login_to_view": "ログインして確認",
        "by_author": "投稿者:",
        "no_articles_yet": "まだ記事が投稿されていません。",
        "no_questions_yet": "まだ質問が投稿されていません。",
        "back_to_articles": "記事一覧に戻る",
        "back_to_qna": "Q&Aフォーラムに戻る",
        "source_link": "ソースリンク",
        "discord_thread_title": "Discord 開発スレッド (コンポーネントV2配信済み)",
        "discord_thread_ko": "韓国語 開発スレッド",
        "discord_thread_en": "英語 開発スレッド",
        "discord_thread_ja": "日本語 開発スレッド",
        "no_comments_yet": "まだコメントがありません。",
        "login_to_comment": "技術ディスカッションに参加するにはDiscordでログインしてください",
        "write_notice_title": "Discordスレッド自動ルーティング:",
        "write_notice_desc": "記事を公開すると、DiscordコンポーネントV2リンク埋め込みを使用して、韓国語、英語、日本語の開発チャンネルに専用スレッドが自動作成されます。",
        "input_title_placeholder": "例: 非同期PythonとPostgreSQLによるマイクロサービス設計",
        "input_tags_placeholder": "python, postgresql, system-design",
        "input_content_placeholder": "Markdown形式で技術的な知見を記述してください...",
        "cancel": "キャンセル",
        "qna_new_desc": "Discordの各言語フォーラムチャンネルに即座に同期される開発質問を投稿します。",
        "qna_new_notice_title": "リアルタイムフォーラム同期:",
        "qna_new_notice_desc": "言語を選択すると、Discordの対応する専用フォーラムチャンネルにスレッドが自動作成されます。",
        "target_forum_label": "対象言語フォーラム *",
        "target_forum_ko": "韓国語 開発 Q&A フォーラム",
        "target_forum_en": "英語 開発 Q&A フォーラム",
        "target_forum_ja": "日本語 開発 Q&A フォーラム",
        "qna_input_title_placeholder": "例: 非同期PostgreSQL接続プールにおける競合状態の解決策は？",
        "qna_input_content_placeholder": "技術的な課題、エラーログ、期待される動作などを詳細に記入してください...",
        "qna_submit_btn": "WebとDiscordに同時投稿",
        "live_in_discord": "この質問はDiscordフォーラムチャンネルとリアルタイム同期しています",
        "no_answers_yet": "まだ回答が投稿されていません。",
        "answer_placeholder": "参考になる技術的な回答を入力してください（Discordフォーラムに自動同期されます）...",
        "login_to_answer": "この質問に回答するにはDiscordでログインしてください",
        "discord_forum_synced": "Discordフォーラム同期済み",
        "footer_text": "© 2026 DevNetwork. エンタープライズDiscord＆GitHubオートメーションアーキテクチャ。"
    }
}

# --- Discord Role / Language Sync ---
async def db_get_user_lang(user_id: int) -> Optional[str]:
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        row = await conn.fetchrow("SELECT lang FROM user_languages WHERE user_id = $1", int(user_id))
        await conn.close()
        return row["lang"] if row else None
    except Exception:
        return None

async def db_set_user_lang(user_id: int, lang: str):
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute("""
            INSERT INTO user_languages (user_id, lang, updated_at)
            VALUES ($1, $2, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id) DO UPDATE SET lang = $2, updated_at = CURRENT_TIMESTAMP
        """, int(user_id), lang)
        await conn.close()
    except Exception:
        pass

async def sync_discord_role(user_id: int, new_lang: str) -> bool:
    if not DISCORD_BOT_TOKEN or not GUILD_ID:
        return False
    target_role_id = ROLE_IDS.get(new_lang)
    if not target_role_id:
        return False

    url_base = f"https://discord.com/api/v10/guilds/{GUILD_ID}/members/{user_id}"
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        async with aiohttp.ClientSession() as session:
            # 1. Fetch current member roles
            async with session.get(url_base, headers=headers) as resp:
                if resp.status != 200:
                    return False
                member_data = await resp.json()
                current_roles = set(int(r) for r in member_data.get("roles", []))

            # 2. Adjust roles
            for l_code, r_id in ROLE_IDS.items():
                if l_code == new_lang:
                    current_roles.add(r_id)
                else:
                    current_roles.discard(r_id)

            # 3. Update member roles
            patch_data = {"roles": list(current_roles)}
            async with session.patch(url_base, headers=headers, json=patch_data) as patch_resp:
                return patch_resp.status in (200, 204)
    except Exception:
        return False

# --- Helper to extract user session ---
def get_session_user(request: Request) -> Optional[Dict[str, Any]]:
    uid = request.cookies.get("dn_user_id")
    uname = request.cookies.get("dn_user_name")
    uavatar = request.cookies.get("dn_user_avatar")
    ulang = request.cookies.get("dn_user_lang")
    if uid and uname:
        return {
            "id": uid,
            "username": uname,
            "avatar_url": uavatar or f"https://cdn.discordapp.com/embed/avatars/{int(uid) % 5}.png",
            "lang": ulang or "ko"
        }
    return None

def resolve_lang(request: Request, user: Optional[Dict[str, Any]]) -> str:
    lang_param = request.query_params.get("lang")
    if lang_param in ("en", "ko", "ja"):
        return lang_param
    cookie_lang = request.cookies.get("dn_lang")
    if cookie_lang in ("en", "ko", "ja"):
        return cookie_lang
    if user and user.get("lang") in ("en", "ko", "ja"):
        return user["lang"]
    return "ko" # Default is Korean!


# ==========================================
# 1. ARTICLES / GEEKNEWS FEED
# ==========================================
@app.get("/", response_class=HTMLResponse)
async def main_page(
    request: Request,
    sort: str = "latest",
    tag: Optional[str] = None,
    lang_filter: Optional[str] = None
):
    user = get_session_user(request)
    ui_lang = resolve_lang(request, user)
    t = TRANSLATIONS.get(ui_lang, TRANSLATIONS["ko"])

    if not user:
        # Non-logged in users see the official DevNetwork Landing Page
        articles_preview = await db_get_articles(limit=4)
        qna_preview = await db_get_qna_posts(limit=4)
        response = templates.TemplateResponse(
            request=request,
            name="landing.html",
            context={
                "user": None,
                "articles_preview": articles_preview,
                "qna_preview": qna_preview,
                "lang": ui_lang,
                "t": t,
                "base_url": APP_BASE_URL
            }
        )
        response.set_cookie(key="dn_lang", value=ui_lang, max_age=31536000, httponly=False)
        return response

    # Logged-in users see the full Articles Feed
    articles = await db_get_articles(sort=sort, tag=tag, lang=lang_filter)
    response = templates.TemplateResponse(
        request=request,
        name="articles.html",
        context={
            "articles": articles,
            "user": user,
            "lang": ui_lang,
            "t": t,
            "current_sort": sort,
            "current_tag": tag or "",
            "current_lang_filter": lang_filter or "all",
            "active_tab": "articles",
            "base_url": APP_BASE_URL
        }
    )
    response.set_cookie(key="dn_lang", value=ui_lang, max_age=31536000, httponly=False)
    return response

@app.get("/articles", response_class=HTMLResponse)
async def articles_page(
    request: Request,
    sort: str = "latest",
    tag: Optional[str] = None,
    lang_filter: Optional[str] = None
):
    user = get_session_user(request)
    if not user:
        return RedirectResponse(url="/auth/discord", status_code=303)

    ui_lang = resolve_lang(request, user)
    t = TRANSLATIONS.get(ui_lang, TRANSLATIONS["ko"])

    articles = await db_get_articles(sort=sort, tag=tag, lang=lang_filter)
    return templates.TemplateResponse(
        request=request,
        name="articles.html",
        context={
            "articles": articles,
            "user": user,
            "lang": ui_lang,
            "t": t,
            "current_sort": sort,
            "current_tag": tag or "",
            "current_lang_filter": lang_filter or "all",
            "active_tab": "articles",
            "base_url": APP_BASE_URL
        }
    )

@app.get("/write", response_class=HTMLResponse)
async def write_article_page(request: Request):
    user = get_session_user(request)
    if not user:
        return RedirectResponse(url="/auth/discord", status_code=303)
    
    ui_lang = resolve_lang(request, user)
    t = TRANSLATIONS.get(ui_lang, TRANSLATIONS["ko"])
    
    return templates.TemplateResponse(
        request=request,
        name="write.html",
        context={
            "user": user,
            "lang": ui_lang,
            "t": t,
            "active_tab": "submit",
            "base_url": APP_BASE_URL
        }
    )

@app.post("/api/article/create")
async def create_article(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    external_url: Optional[str] = Form(""),
    tags: Optional[str] = Form(""),
    image_url: Optional[str] = Form("")
):
    user = get_session_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    ui_lang = resolve_lang(request, user)
    
    # 1. Generate multilang titles and summaries
    summaries = await generate_multilang_summaries(title, content)
    primary_summary = summaries.get(ui_lang, {}).get("summary", content[:300])

    # 2. Insert into DB
    article_id = await db_create_article(
        author_id=user["id"],
        author_name=user["username"],
        author_avatar=user["avatar_url"],
        title=title,
        content=content,
        summary=primary_summary,
        external_url=external_url or "",
        image_url=image_url or "",
        tags=tags or "",
        lang=ui_lang
    )

    # 3. Create Discord Threads in all 3 language developer channels concurrently
    thread_tasks = []
    for l_code in ("ko", "en", "ja"):
        loc_title = summaries.get(l_code, {}).get("title", title)
        loc_summary = summaries.get(l_code, {}).get("summary", primary_summary)
        thread_tasks.append(
            discord_create_article_thread(
                lang=l_code,
                title=loc_title,
                summary=loc_summary,
                article_id=article_id,
                image_url=image_url
            )
        )
    
    results = await asyncio.gather(*thread_tasks, return_exceptions=True)
    for res in results:
        if isinstance(res, dict) and res.get("thread_id"):
            await db_save_article_thread(
                article_id=article_id,
                lang=res["lang"],
                channel_id=res["channel_id"],
                thread_id=res["thread_id"],
                message_id=res.get("message_id", "")
            )

    return RedirectResponse(url=f"/article/{article_id}", status_code=303)

@app.get("/article/{article_id}", response_class=HTMLResponse)
async def article_detail(request: Request, article_id: int):
    user = get_session_user(request)
    user_agent = request.headers.get("user-agent", "").lower()

    # Discord crawler or bot can preview the meta tags & component embeds
    is_crawler = any(b in user_agent for b in ("discord", "bot", "crawler", "spider", "twitter"))
    if not user and not is_crawler:
        return RedirectResponse(url="/auth/discord", status_code=303)

    ui_lang = resolve_lang(request, user)
    t = TRANSLATIONS.get(ui_lang, TRANSLATIONS["ko"])

    article = await db_get_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    threads = await db_get_article_threads(article_id)
    comments = await db_get_article_comments(article_id)
    content_html = markdown.markdown(article["content"], extensions=["fenced_code", "tables"])

    return templates.TemplateResponse(
        request=request,
        name="article_detail.html",
        context={
            "article": article,
            "content_html": content_html,
            "threads": threads,
            "comments": comments,
            "user": user,
            "lang": ui_lang,
            "t": t,
            "base_url": APP_BASE_URL,
            "active_tab": "articles"
        }
    )

@app.post("/api/article/{article_id}/upvote")
async def toggle_article_upvote(request: Request, article_id: int):
    user = get_session_user(request)
    if not user:
        return JSONResponse({"error": "Login required"}, status_code=401)
    
    res = await db_toggle_upvote(article_id, user["id"])
    return JSONResponse(res)

@app.post("/api/article/{article_id}/comment")
async def add_article_comment(
    request: Request,
    article_id: int,
    content: str = Form(...)
):
    user = get_session_user(request)
    if not user:
        return RedirectResponse(url="/auth/discord", status_code=303)
    
    if content.strip():
        await db_add_article_comment(
            article_id=article_id,
            author_id=user["id"],
            author_name=user["username"],
            author_avatar=user["avatar_url"],
            content=content.strip()
        )
    return RedirectResponse(url=f"/article/{article_id}", status_code=303)


# ==========================================
# 2. Q&A FORUM (Web <-> Discord Forum Sync)
# ==========================================
@app.get("/qna", response_class=HTMLResponse)
async def qna_feed(
    request: Request,
    lang_filter: Optional[str] = None,
    solved_filter: Optional[str] = None
):
    user = get_session_user(request)
    if not user:
        return RedirectResponse(url="/auth/discord", status_code=303)

    ui_lang = resolve_lang(request, user)
    t = TRANSLATIONS.get(ui_lang, TRANSLATIONS["ko"])

    is_solved = None
    if solved_filter == "solved":
        is_solved = True
    elif solved_filter == "open":
        is_solved = False

    posts = await db_get_qna_posts(lang=lang_filter, solved=is_solved)

    return templates.TemplateResponse(
        request=request,
        name="qna_list.html",
        context={
            "posts": posts,
            "user": user,
            "lang": ui_lang,
            "t": t,
            "current_lang_filter": lang_filter or "all",
            "current_solved_filter": solved_filter or "all",
            "active_tab": "qna",
            "base_url": APP_BASE_URL
        }
    )

@app.get("/qna/new", response_class=HTMLResponse)
async def new_qna_page(request: Request):
    user = get_session_user(request)
    if not user:
        return RedirectResponse(url="/auth/discord", status_code=303)

    ui_lang = resolve_lang(request, user)
    t = TRANSLATIONS.get(ui_lang, TRANSLATIONS["ko"])

    return templates.TemplateResponse(
        request=request,
        name="qna_new.html",
        context={
            "user": user,
            "lang": ui_lang,
            "t": t,
            "active_tab": "qna",
            "base_url": APP_BASE_URL
        }
    )

@app.post("/api/qna/create")
async def create_qna(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    post_lang: str = Form("en"),
    image_url: Optional[str] = Form("")
):
    user = get_session_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    forum_channel_id = str(QNA_FORUM_CHANNELS.get(post_lang, QNA_FORUM_CHANNELS["en"]))

    # 1. Insert into DB first
    post_id = await db_create_qna_post(
        author_id=user["id"],
        author_name=user["username"],
        author_avatar=user["avatar_url"],
        lang=post_lang,
        title=title,
        content=content,
        image_url=image_url or "",
        discord_channel_id=forum_channel_id,
        discord_thread_id=""
    )

    # 2. Create Forum Post in Discord
    thread_id = await discord_create_forum_post(
        lang=post_lang,
        title=title,
        content=content,
        post_id=post_id,
        image_url=image_url
    )
    if thread_id:
        await db_update_qna_discord_thread(post_id, thread_id)

    return RedirectResponse(url=f"/qna/{post_id}", status_code=303)

@app.get("/qna/{post_id}", response_class=HTMLResponse)
async def qna_detail(request: Request, post_id: int):
    user = get_session_user(request)
    user_agent = request.headers.get("user-agent", "").lower()
    is_crawler = any(b in user_agent for b in ("discord", "bot", "crawler", "spider", "twitter"))
    if not user and not is_crawler:
        return RedirectResponse(url="/auth/discord", status_code=303)

    ui_lang = resolve_lang(request, user)
    t = TRANSLATIONS.get(ui_lang, TRANSLATIONS["ko"])

    post = await db_get_qna_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Q&A Post not found")

    answers = await db_get_qna_answers(post_id)
    content_html = markdown.markdown(post["content"], extensions=["fenced_code", "tables"])

    return templates.TemplateResponse(
        request=request,
        name="qna_detail.html",
        context={
            "post": post,
            "content_html": content_html,
            "answers": answers,
            "user": user,
            "lang": ui_lang,
            "t": t,
            "active_tab": "qna",
            "base_url": APP_BASE_URL
        }
    )

@app.post("/api/qna/{post_id}/answer")
async def add_qna_answer(
    request: Request,
    post_id: int,
    content: str = Form(...)
):
    user = get_session_user(request)
    if not user:
        return RedirectResponse(url="/auth/discord", status_code=303)

    post = await db_get_qna_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Q&A Post not found")

    discord_msg_id = None
    if post.get("discord_thread_id"):
        discord_msg_id = await discord_send_thread_message(
            thread_id=post["discord_thread_id"],
            author_name=user["username"],
            content=content.strip()
        )

    await db_add_qna_answer(
        post_id=post_id,
        author_id=user["id"],
        author_name=user["username"],
        author_avatar=user["avatar_url"],
        content=content.strip(),
        discord_message_id=discord_msg_id
    )
    return RedirectResponse(url=f"/qna/{post_id}", status_code=303)

@app.get("/api/qna/sync")
async def trigger_discord_qna_sync():
    """Fetches threads from Discord forum channels and syncs them into Neon DB."""
    synced_count = 0
    for lang, forum_id in QNA_FORUM_CHANNELS.items():
        threads = await discord_fetch_forum_threads(forum_id)
        for th in threads:
            thread_id = th["id"]
            name = th.get("name", "Discord Q&A Discussion")
            owner_id = th.get("owner_id", "0")
            created_at = datetime.fromisoformat(th["thread_metadata"]["create_timestamp"].replace("Z", "+00:00")) if "create_timestamp" in th.get("thread_metadata", {}) else datetime.utcnow()
            
            await db_upsert_discord_forum_thread(
                lang=lang,
                channel_id=str(forum_id),
                thread_id=str(thread_id),
                name=name,
                author_id=str(owner_id),
                author_name="Discord Member",
                author_avatar="",
                created_at=created_at
            )
            synced_count += 1
            
    return JSONResponse({"status": "ok", "synced_threads": synced_count})


# ==========================================
# 3. OAUTH2 & ROLE LANGUAGE SWITCHING
# ==========================================
@app.get("/auth/discord")
async def auth_discord():
    redirect_uri = DISCORD_REDIRECT_URI
    scope = "identify guilds.members.read"
    url = f"https://discord.com/api/oauth2/authorize?client_id={DISCORD_CLIENT_ID}&redirect_uri={redirect_uri}&response_type=code&scope={scope}"
    return RedirectResponse(url=url)

@app.get("/auth/discord/callback")
@app.get("/auth/callback")
async def auth_callback(code: str, request: Request):
    redirect_uri = DISCORD_REDIRECT_URI
    token_url = "https://discord.com/api/oauth2/token"
    data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    async with aiohttp.ClientSession() as session:
        async with session.post(token_url, data=data, headers=headers) as resp:
            if resp.status != 200:
                raise HTTPException(status_code=400, detail="Failed to retrieve token from Discord")
            token_json = await resp.json()
            access_token = token_json.get("access_token")

        user_headers = {"Authorization": f"Bearer {access_token}"}
        async with session.get("https://discord.com/api/v10/users/@me", headers=user_headers) as u_resp:
            if u_resp.status != 200:
                raise HTTPException(status_code=400, detail="Failed to fetch user data")
            user_data = await u_resp.json()

        member_headers = {"Authorization": f"Bot {DISCORD_BOT_TOKEN}"}
        user_id = user_data["id"]
        role_detected_lang = None
        async with session.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/members/{user_id}", headers=member_headers) as m_resp:
            if m_resp.status == 200:
                m_data = await m_resp.json()
                user_roles = [int(r) for r in m_data.get("roles", [])]
                for l_code, r_id in ROLE_IDS.items():
                    if r_id in user_roles:
                        role_detected_lang = l_code
                        break

    db_lang = await db_get_user_lang(int(user_id))
    final_lang = role_detected_lang or db_lang or "en"
    await db_set_user_lang(int(user_id), final_lang)

    response = RedirectResponse(url=f"/?lang={final_lang}")
    response.set_cookie(key="dn_user_id", value=user_data["id"], max_age=86400*30, httponly=False)
    response.set_cookie(key="dn_user_name", value=user_data["username"], max_age=86400*30, httponly=False)
    avatar_url = f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png" if user_data.get("avatar") else ""
    response.set_cookie(key="dn_user_avatar", value=avatar_url, max_age=86400*30, httponly=False)
    response.set_cookie(key="dn_user_lang", value=final_lang, max_age=86400*30, httponly=False)
    response.set_cookie(key="dn_lang", value=final_lang, max_age=86400*30, httponly=False)
    return response

@app.get("/auth/logout")
async def auth_logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("dn_user_id")
    response.delete_cookie("dn_user_name")
    response.delete_cookie("dn_user_avatar")
    response.delete_cookie("dn_user_lang")
    return response

@app.post("/api/user/language")
async def set_user_language(request: Request):
    user = get_session_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    body = await request.json()
    new_lang = body.get("lang")
    if new_lang not in ("ko", "en", "ja"):
        raise HTTPException(status_code=400, detail="Invalid language")

    await db_set_user_lang(int(user["id"]), new_lang)
    await sync_discord_role(int(user["id"]), new_lang)

    response = JSONResponse({"status": "success", "lang": new_lang})
    response.set_cookie(key="dn_user_lang", value=new_lang, max_age=86400*30, httponly=False)
    response.set_cookie(key="dn_lang", value=new_lang, max_age=86400*30, httponly=False)
    return response

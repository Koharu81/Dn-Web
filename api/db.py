import os
import asyncpg
from typing import List, Dict, Any, Optional

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://neondb_owner:npg_Zla3NzLDfK6M@ep-odd-lake-b58efh05-pooler.c-7.us-east-2.aws.neon.tech/neondb?sslmode=require")

async def get_db_connection():
    return await asyncpg.connect(DATABASE_URL)

# --- Articles ---
async def db_get_articles(sort: str = "latest", tag: Optional[str] = None, lang: Optional[str] = None, limit: int = 40, offset: int = 0) -> List[Dict[str, Any]]:
    conn = await get_db_connection()
    try:
        query = """
            SELECT a.*, 
                   COUNT(DISTINCT c.id) as comment_count,
                   ARRAY_AGG(DISTINCT t.lang) FILTER (WHERE t.lang IS NOT NULL) as linked_langs
            FROM articles a
            LEFT JOIN article_comments c ON a.id = c.article_id
            LEFT JOIN article_threads t ON a.id = t.article_id
        """
        clauses = []
        params = []
        if tag:
            params.append(f"%{tag.lower()}%")
            clauses.append(f"LOWER(a.tags) LIKE ${len(params)}")
        if lang and lang != "all":
            params.append(lang)
            clauses.append(f"a.lang = ${len(params)}")

        if clauses:
            query += " WHERE " + " AND ".join(clauses)

        query += " GROUP BY a.id "
        if sort == "popular":
            query += " ORDER BY a.upvotes DESC, a.created_at DESC "
        else:
            query += " ORDER BY a.created_at DESC "

        params.extend([limit, offset])
        query += f" LIMIT ${len(params)-1} OFFSET ${len(params)}"

        rows = await conn.fetch(query, *params)
        return [dict(r) for r in rows]
    finally:
        await conn.close()

async def db_get_article(article_id: int) -> Optional[Dict[str, Any]]:
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow("""
            SELECT a.*, COUNT(DISTINCT c.id) as comment_count
            FROM articles a
            LEFT JOIN article_comments c ON a.id = c.article_id
            WHERE a.id = $1
            GROUP BY a.id
        """, article_id)
        return dict(row) if row else None
    finally:
        await conn.close()

async def db_create_article(author_id: str, author_name: str, author_avatar: str, title: str, content: str, summary: str, external_url: str, image_url: str, tags: str, lang: str) -> int:
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow("""
            INSERT INTO articles (author_id, author_name, author_avatar, title, content, summary, external_url, image_url, tags, lang)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id
        """, author_id, author_name, author_avatar, title, content, summary, external_url, image_url, tags, lang)
        return row["id"]
    finally:
        await conn.close()

async def db_save_article_thread(article_id: int, lang: str, channel_id: str, thread_id: str, message_id: str):
    conn = await get_db_connection()
    try:
        await conn.execute("""
            INSERT INTO article_threads (article_id, lang, channel_id, thread_id, message_id)
            VALUES ($1, $2, $3, $4, $5)
        """, article_id, lang, channel_id, thread_id, message_id)
    finally:
        await conn.close()

async def db_get_article_threads(article_id: int) -> List[Dict[str, Any]]:
    conn = await get_db_connection()
    try:
        rows = await conn.fetch("SELECT * FROM article_threads WHERE article_id = $1 ORDER BY id ASC", article_id)
        return [dict(r) for r in rows]
    finally:
        await conn.close()

async def db_toggle_upvote(article_id: int, user_id: str) -> Dict[str, Any]:
    conn = await get_db_connection()
    try:
        exists = await conn.fetchrow("SELECT 1 FROM article_upvotes WHERE article_id = $1 AND user_id = $2", article_id, user_id)
        if exists:
            await conn.execute("DELETE FROM article_upvotes WHERE article_id = $1 AND user_id = $2", article_id, user_id)
            await conn.execute("UPDATE articles SET upvotes = GREATEST(0, upvotes - 1) WHERE id = $1", article_id)
            voted = False
        else:
            await conn.execute("INSERT INTO article_upvotes (article_id, user_id) VALUES ($1, $2)", article_id, user_id)
            await conn.execute("UPDATE articles SET upvotes = upvotes + 1 WHERE id = $1", article_id)
            voted = True
        
        row = await conn.fetchrow("SELECT upvotes FROM articles WHERE id = $1", article_id)
        return {"voted": voted, "upvotes": row["upvotes"] if row else 0}
    finally:
        await conn.close()

async def db_get_article_comments(article_id: int) -> List[Dict[str, Any]]:
    conn = await get_db_connection()
    try:
        rows = await conn.fetch("SELECT * FROM article_comments WHERE article_id = $1 ORDER BY created_at ASC", article_id)
        return [dict(r) for r in rows]
    finally:
        await conn.close()

async def db_add_article_comment(article_id: int, author_id: str, author_name: str, author_avatar: str, content: str) -> Dict[str, Any]:
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow("""
            INSERT INTO article_comments (article_id, author_id, author_name, author_avatar, content)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
        """, article_id, author_id, author_name, author_avatar, content)
        return dict(row)
    finally:
        await conn.close()


# --- Q&A Posts ---
async def db_get_qna_posts(sort: str = "latest", lang: Optional[str] = None, solved: Optional[bool] = None, limit: int = 40, offset: int = 0) -> List[Dict[str, Any]]:
    conn = await get_db_connection()
    try:
        query = """
            SELECT q.*, COUNT(a.id) as answer_count
            FROM qna_posts q
            LEFT JOIN qna_answers a ON q.id = a.post_id
        """
        clauses = []
        params = []
        if lang and lang != "all":
            params.append(lang)
            clauses.append(f"q.lang = ${len(params)}")
        if solved is not None:
            params.append(solved)
            clauses.append(f"q.solved = ${len(params)}")
            
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
            
        query += " GROUP BY q.id "
        if sort == "popular":
            query += " ORDER BY COUNT(a.id) DESC, q.created_at DESC "
        else:
            query += " ORDER BY q.created_at DESC "

        params.extend([limit, offset])
        query += f" LIMIT ${len(params)-1} OFFSET ${len(params)}"
        
        rows = await conn.fetch(query, *params)
        return [dict(r) for r in rows]
    finally:
        await conn.close()

async def db_get_qna_post(post_id: int) -> Optional[Dict[str, Any]]:
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow("""
            SELECT q.*, COUNT(a.id) as answer_count
            FROM qna_posts q
            LEFT JOIN qna_answers a ON q.id = a.post_id
            WHERE q.id = $1
            GROUP BY q.id
        """, post_id)
        return dict(row) if row else None
    finally:
        await conn.close()

async def db_create_qna_post(author_id: str, author_name: str, author_avatar: str, lang: str, title: str, content: str, image_url: str, discord_channel_id: str, discord_thread_id: str) -> int:
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow("""
            INSERT INTO qna_posts (author_id, author_name, author_avatar, lang, title, content, image_url, discord_channel_id, discord_thread_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
        """, author_id, author_name, author_avatar, lang, title, content, image_url, discord_channel_id, discord_thread_id)
        return row["id"]
    finally:
        await conn.close()

async def db_update_qna_discord_thread(post_id: int, thread_id: str):
    conn = await get_db_connection()
    try:
        await conn.execute("UPDATE qna_posts SET discord_thread_id = $1 WHERE id = $2", thread_id, post_id)
    finally:
        await conn.close()

async def db_get_qna_answers(post_id: int) -> List[Dict[str, Any]]:
    conn = await get_db_connection()
    try:
        rows = await conn.fetch("SELECT * FROM qna_answers WHERE post_id = $1 ORDER BY created_at ASC", post_id)
        return [dict(r) for r in rows]
    finally:
        await conn.close()

async def db_add_qna_answer(post_id: int, author_id: str, author_name: str, author_avatar: str, content: str, discord_message_id: Optional[str] = None) -> Dict[str, Any]:
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow("""
            INSERT INTO qna_answers (post_id, author_id, author_name, author_avatar, content, discord_message_id)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING *
        """, post_id, author_id, author_name, author_avatar, content, discord_message_id)
        return dict(row)
    finally:
        await conn.close()

async def db_upsert_discord_forum_thread(lang: str, channel_id: str, thread_id: str, name: str, author_id: str, author_name: str, author_avatar: str, created_at):
    conn = await get_db_connection()
    try:
        # Check if already exists
        exists = await conn.fetchrow("SELECT id FROM qna_posts WHERE discord_thread_id = $1", str(thread_id))
        if not exists:
            await conn.execute("""
                INSERT INTO qna_posts (author_id, author_name, author_avatar, lang, title, content, image_url, discord_channel_id, discord_thread_id, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, '', $7, $8, $9)
            """, str(author_id), author_name or "Discord Member", author_avatar or "", lang, name, "(Discussed on Discord Forum)", str(channel_id), str(thread_id), created_at)
    finally:
        await conn.close()

# --- GitHub Repos & Webhook ---
async def db_get_github_session(token: str) -> Optional[Dict[str, Any]]:
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow("SELECT * FROM github_repos WHERE token = $1", token)
        if not row:
            return None
        data = dict(row)
        if isinstance(data.get("invited_members"), str):
            try:
                data["invited_members"] = json.loads(data["invited_members"])
            except Exception:
                pass
        return data
    finally:
        await conn.close()

async def db_get_github_repo_by_name(repo_name: str) -> Optional[Dict[str, Any]]:
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow("SELECT * FROM github_repos WHERE LOWER(repo) = LOWER($1) ORDER BY created_at DESC LIMIT 1", repo_name)
        return dict(row) if row else None
    finally:
        await conn.close()

async def db_update_github_repo_thread(token: str, thread_id: int):
    conn = await get_db_connection()
    try:
        await conn.execute("UPDATE github_repos SET thread_id = $1 WHERE token = $2", int(thread_id), token)
    finally:
        await conn.close()


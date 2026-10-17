import os
import aiohttp
from typing import Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="DevNetwork Global Portal")

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/static/style.css")
@app.get("/style.css")
async def get_style_css():
    css_file = os.path.join(STATIC_DIR, "style.css")
    if os.path.exists(css_file):
        with open(css_file, "r", encoding="utf-8") as f:
            return Response(content=f.read(), media_type="text/css")
    return Response(content="", media_type="text/css")

templates = Jinja2Templates(directory=TEMPLATES_DIR)

DISCORD_BOT_TOKEN = os.getenv("DN_DISCORD_BOT_TOKEN", "")
DISCORD_CLIENT_ID = os.getenv("DN_CLIENT_ID", "")
DISCORD_CLIENT_SECRET = os.getenv("DN_CLIENT_SECRET", "")
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")

GUILD_ID = 1552469048099471390
ROLE_IDS = {
    "ko": 1555128535989882910, # 한국어
    "en": 1555128570634829884, # English
    "ja": 1555128606513168447  # 日本語
}

TRANSLATIONS = {
    "ko": {
        "login_discord": "디스코드 로그인",
        "pill_text": "DevNetwork 글로벌 개발자 포털 & 봇 관제 센터",
        "hero_title": "글로벌 IT 커뮤니티를 위한\n차세대 엔지니어링 허브",
        "hero_desc": "한국어, 영어, 일본어 3개 언어로 상호 연결되는 글로벌 개발자 네트워크. 엄격한 Components V2 아키텍처와 엔터프라이즈 수준의 GitHub & DevOps 인프라를 제공합니다.",
        "switch_role_lang": "메인 언어 역할 변경",
        "modal_title": "메인 언어 역할을 선택해주세요",
        "modal_desc": "DevNetwork 커뮤니티에서 활동하실 주 언어를 선택하시면 디스코드 서버 역할이 자동으로 동기화됩니다.",
        "close": "닫기",
        "f001_title": "실시간 메시지 번역",
        "f001_desc": "메시지 입력 또는 우클릭 컨텍스트 메뉴로 한국어, 영어, 일본어 상호 실시간 AI 번역을 제공합니다.",
        "f004_title": "개발자 용어 사전",
        "f004_desc": "DuckDuckGo 실시간 웹 검색과 결합하여 IT/개발 전문 용어의 3개 국어 표준 정의와 실무 예제를 제공합니다.",
        "f017_title": "글로벌 뉴스 채널 라우팅",
        "f017_desc": "GeekNews, Hacker News, Zenn 등 글로벌 테크 RSS 피드를 각 언어별 채널로 자동 번역하여 정기 발행합니다.",
        "f032_title": "코드 블록 자동 포맷터",
        "f032_desc": "들여쓰기가 깨진 코드를 감지하여 Black(Python) 및 Prettier 스타일로 완벽하게 재정렬하고 Diff를 비교합니다.",
        "f091_title": "패키지 버전 조회",
        "f091_desc": "npm, pip, cargo, go 생태계 라이브러리의 최신 안정화 버전, 라이선스, 다운로드 지표를 실시간 검사합니다.",
        "f096_title": "Base64 인코더/디코더",
        "f096_desc": "텍스트 및 데이터 스니펫을 원클릭으로 Base64 상호 변환하고 클립보드 복사 블록을 지원합니다.",
        "f098_title": "DNS & WHOIS 조회",
        "f098_desc": "글로벌 도메인의 A, CNAME, MX 레코드와 네임서버 전파 상태 및 GeoIP 인프라 위치를 진단합니다.",
        "f120_title": "HTTP 요청 모의 테스트",
        "f120_desc": "봇 서버에서 직접 엔드포인트로 경량 HTTP GET/POST 테스트 요청을 전송하여 상태 코드와 헤더를 점검합니다.",
        "f126_title": "GitHub 저장소 포럼 연동",
        "f126_desc": "국가별 전용 포럼 포스트 생성, 실시간 알림 토글 패널 제어 및 1주일 주기 정기 보안 리포트를 발송합니다."
    },
    "en": {
        "login_discord": "Login with Discord",
        "pill_text": "DevNetwork Global Engineering Portal & Sentinel",
        "hero_title": "Next-Gen Engineering Hub\nfor Global Developers",
        "hero_desc": "Connecting developers worldwide across Korean, English, and Japanese. Built on strict Discord Components V2 specifications and enterprise GitHub infrastructure.",
        "switch_role_lang": "Change Language Role",
        "modal_title": "Select Your Primary Language",
        "modal_desc": "Choose your primary language for the DevNetwork community. Your Discord server role will be updated instantly.",
        "close": "Close",
        "f001_title": "Real-time Message Translation",
        "f001_desc": "Instant bidirectional AI translation between Korean, English, and Japanese with context menu support.",
        "f004_title": "Tech Dictionary",
        "f004_desc": "Real-time DuckDuckGo search combined with AI to deliver concise 3-language technical definitions and snippets.",
        "f017_title": "Global News Router",
        "f017_desc": "Curated RSS feeds from Hacker News, GeekNews, and Zenn translated and routed to dedicated language channels.",
        "f032_title": "Code Auto Formatter",
        "f032_desc": "Auto-detect and reformat messy code snippets with Black (Python) and Prettier style, including Diff inspection.",
        "f091_title": "Package Version Inspector",
        "f091_desc": "Instant lookup of latest stable versions, licenses, and weekly downloads for npm, pip, cargo, and go modules.",
        "f096_title": "Base64 Encoder/Decoder",
        "f096_desc": "Seamless two-way Base64 encoding/decoding with one-tap clipboard copy blocks.",
        "f098_title": "DNS & Domain Lookup",
        "f098_desc": "Live DNS record verification (A, CNAME, MX, NS) and GeoIP hosting infrastructure diagnostics.",
        "f120_title": "HTTP Request Tester",
        "f120_desc": "Direct lightweight HTTP GET/POST simulation from the bot server to inspect headers and response bodies.",
        "f126_title": "GitHub Repository Bridge",
        "f126_desc": "Dedicated forum threads with persistent toggle panels, member invitations, and automated weekly security audits."
    },
    "ja": {
        "login_discord": "Discordでログイン",
        "pill_text": "DevNetwork グローバル開発者ポータル ＆ Bot管制センター",
        "hero_title": "世界中のエンジニアを繋ぐ\n次世代開発者コミュニティ",
        "hero_desc": "日本語、韓国語、英語の3言語で繋がるグローバルITコミュニティ。Discord Components V2の最新仕様とGitHub・DevOps自動化インフラを提供します。",
        "switch_role_lang": "メイン言語ロールの変更",
        "modal_title": "メイン言語ロールを選択してください",
        "modal_desc": "DevNetworkコミュニティで利用する主言語を選択してください。Discordサーバーのロールが自動的に同期されます。",
        "close": "閉じる",
        "f001_title": "リアルタイムメッセージ翻訳",
        "f001_desc": "日本語・韓国語・英語の相互翻訳を即座に実行。メッセージ右クリックのコンテキストメニューにも対応。",
        "f004_title": "開発者用語辞典",
        "f004_desc": "DuckDuckGoリアルタイム検索とAI要約を融合し、IT専門用語の3言語定義および実務コード例を案内。",
        "f017_title": "グローバルニュース自動配信",
        "f017_desc": "Zenn、Hacker News、GeekNews等の技術RSSを各言語チャンネルへ自動翻訳ルーティング配信。",
        "f032_title": "コード自動フォーマッター",
        "f032_desc": "崩れたインデントを検知し、Black(Python)やPrettier形式で綺麗に再整列。差分(Diff)比較も可能。",
        "f091_title": "パッケージバージョン照会",
        "f091_desc": "npm、pip、cargo、go各エコシステムの最新安定バージョン、ライセンス、ダウンロード数を即座に確認。",
        "f096_title": "Base64 エンコーダー/デコーダー",
        "f096_desc": "テキストやデータをBase64へ即座に相互変換し、ワンタップコピー用ブロックを提供。",
        "f098_title": "DNS＆ドメイン照会",
        "f098_desc": "A、CNAME、MX、NSレコードの伝播状況およびホスティングインフラのGeoIP詳細を診断。",
        "f120_title": "HTTPリクエスト模擬テスト",
        "f120_desc": "Botサーバーから対象APIエンドポイントへ直接テストリクエストを送信し、ステータスコードを診断。",
        "f126_title": "GitHubリポジトリ連動",
        "f126_desc": "国別フォーラム投稿の自動生成、常設トグルパネル、メンバー招待、および週次セキュリティレポート配信。"
    }
}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    lang = request.query_params.get("lang")
    user_session = request.cookies.get("dn_user_id")

    user_info = None
    show_modal = False

    if user_session:
        user_id = int(user_session)
        saved_lang = request.cookies.get("dn_user_lang")
        username = request.cookies.get("dn_username", "Developer")
        avatar = request.cookies.get("dn_avatar", "https://cdn.discordapp.com/embed/avatars/0.png")

        user_info = {
            "id": user_id,
            "username": username,
            "avatar_url": avatar,
            "lang": saved_lang
        }

        if not lang and saved_lang:
            lang = saved_lang
        elif not saved_lang:
            show_modal = True

    if not lang or lang not in TRANSLATIONS:
        lang = "ko"

    response = templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "lang": lang,
            "user": user_info,
            "show_lang_modal": show_modal,
            "t": TRANSLATIONS[lang]
        }
    )
    response.set_cookie("dn_lang", lang, max_age=86400 * 30)
    return response

@app.get("/auth/discord")
async def discord_login():
    redirect_uri = "https://dn.koharu.live/auth/discord/callback"
    auth_url = (
        f"https://discord.com/api/oauth2/authorize?client_id={DISCORD_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}&response_type=code&scope=identify%20guilds"
    )
    return RedirectResponse(auth_url)

@app.get("/auth/discord/callback")
async def discord_callback(code: Optional[str] = None):
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    redirect_uri = "https://dn.koharu.live/auth/discord/callback"
    token_url = "https://discord.com/api/oauth2/token"
    data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(token_url, data=data) as resp:
            if resp.status != 200:
                return RedirectResponse("/?error=token_exchange_failed")
            token_data = await resp.json()
            access_token = token_data.get("access_token")

        headers = {"Authorization": f"Bearer {access_token}"}
        async with session.get("https://discord.com/api/users/@me", headers=headers) as resp:
            if resp.status != 200:
                return RedirectResponse("/?error=user_fetch_failed")
            user_data = await resp.json()

    user_id = int(user_data["id"])
    username = user_data["username"]
    avatar_hash = user_data.get("avatar")
    avatar_url = (
        f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png"
        if avatar_hash else "https://cdn.discordapp.com/embed/avatars/0.png"
    )

    detected_lang = None
    if DISCORD_BOT_TOKEN:
        bot_headers = {"Authorization": f"Bot {DISCORD_BOT_TOKEN}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/members/{user_id}", headers=bot_headers) as mresp:
                if mresp.status == 200:
                    member_data = await mresp.json()
                    roles = member_data.get("roles", [])
                    for l_code, r_id in ROLE_IDS.items():
                        if str(r_id) in roles or r_id in roles:
                            detected_lang = l_code
                            break

    target_lang = detected_lang or "ko"
    response = RedirectResponse(f"/?lang={target_lang}")
    response.set_cookie("dn_user_id", str(user_id), max_age=86400 * 7)
    response.set_cookie("dn_username", username, max_age=86400 * 7)
    response.set_cookie("dn_avatar", avatar_url, max_age=86400 * 7)
    if detected_lang:
        response.set_cookie("dn_user_lang", detected_lang, max_age=86400 * 30)
    response.set_cookie("dn_lang", target_lang, max_age=86400 * 30)
    return response

@app.post("/api/user/language")
async def update_user_language(request: Request):
    user_id_cookie = request.cookies.get("dn_user_id")
    if not user_id_cookie:
        return JSONResponse({"status": "guest_only"}, status_code=200)

    user_id = int(user_id_cookie)
    body = await request.json()
    new_lang = body.get("lang")
    if new_lang not in ROLE_IDS:
        raise HTTPException(status_code=400, detail="Invalid language code")

    if DISCORD_BOT_TOKEN:
        bot_headers = {"Authorization": f"Bot {DISCORD_BOT_TOKEN}"}
        async with aiohttp.ClientSession() as session:
            for l_code, r_id in ROLE_IDS.items():
                if l_code != new_lang:
                    await session.delete(
                        f"https://discord.com/api/v10/guilds/{GUILD_ID}/members/{user_id}/roles/{r_id}",
                        headers=bot_headers
                    )
            target_role = ROLE_IDS[new_lang]
            await session.put(
                f"https://discord.com/api/v10/guilds/{GUILD_ID}/members/{user_id}/roles/{target_role}",
                headers=bot_headers
            )

    resp = JSONResponse({"status": "success", "lang": new_lang})
    resp.set_cookie("dn_user_lang", new_lang, max_age=86400 * 30)
    resp.set_cookie("dn_lang", new_lang, max_age=86400 * 30)
    return resp

@app.get("/github/{token}", response_class=HTMLResponse)
async def github_connect_page(request: Request, token: str):
    redirect_uri = "https://dn.koharu.live/github/callback"
    return templates.TemplateResponse(
        request=request,
        name="github_connect.html",
        context={
            "repo": "DevNetwork Repository",
            "token": token,
            "github_client_id": GITHUB_CLIENT_ID,
            "redirect_uri": redirect_uri
        }
    )

@app.get("/github/callback")
async def github_callback(code: Optional[str] = None, state: Optional[str] = None):
    if not code:
        return RedirectResponse("/?error=missing_github_code")
    if state:
        return RedirectResponse(f"/github/{state}?connected=true")
    return RedirectResponse("/?connected=true")

@app.post("/api/webhook/github")
async def github_webhook(request: Request):
    event = request.headers.get("X-GitHub-Event", "ping")
    if event == "ping":
        return JSONResponse({"msg": "pong"})
    return JSONResponse({"status": "received", "event": event})

@app.get("/auth/logout")
async def logout():
    response = RedirectResponse("/")
    response.delete_cookie("dn_user_id")
    response.delete_cookie("dn_username")
    response.delete_cookie("dn_avatar")
    response.delete_cookie("dn_user_lang")
    return response

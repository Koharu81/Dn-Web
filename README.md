# DevNetwork Web Portal (Dn-Web)

DevNetwork 글로벌 IT 커뮤니티 공식 웹 포털 및 관제 대시보드입니다. Vercel Serverless Functions(Python FastAPI) 환경에 최적화되어 있습니다.

## 🚀 Vercel 배포 가이드

### 1. Vercel 프로젝트 생성
1. [Vercel 대시보드](https://vercel.com)에 로그인합니다.
2. **Add New...** ➔ **Project** 를 선택하고 `Koharu81/Dn-Web` 저장소를 가져옵니다 (Import).

### 2. 빌드 및 프로젝트 설정
Vercel 설정 화면에서 아래와 같이 지정합니다:
- **Framework Preset**: `Other`
- **Root Directory**: `./`
- **Build Command**: 비워둠 (Leave empty / 기본값)
- **Output Directory**: 비워둠 (Leave empty / 기본값)
- **Install Command**: `pip install -r requirements.txt` (Vercel이 자동 인식)

### 3. 환경 변수 (Environment Variables) 설정
Vercel 프로젝트의 **Settings ➔ Environment Variables** 에서 다음 키와 값을 등록합니다:

| 키 | 설명 |
| :--- | :--- |
| `DN_DISCORD_BOT_TOKEN` | 디스코드 봇 토큰 (역할 부여용) |
| `DN_CLIENT_ID` | 디스코드 OAuth 클라이언트 ID |
| `DN_CLIENT_SECRET` | 디스코드 OAuth 클라이언트 시크릿 |
| `GITHUB_CLIENT_ID` | GitHub OAuth 클라이언트 ID |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth 클라이언트 시크릿 |

### 4. 커스텀 도메인 설정
1. Vercel 프로젝트 **Settings ➔ Domains** 로 이동합니다.
2. `dn.koharu.live` 도메인을 추가하고 안내되는 CNAME 레코드(`cname.vercel-dns.com`)를 DNS에 바인딩합니다.

---

## 🔑 OAuth & Webhook 콜백 URL
- **Discord OAuth2 Redirect URI:**  
  `https://dn.koharu.live/auth/discord/callback`
- **GitHub OAuth App Authorization Callback URL:**  
  `https://dn.koharu.live/github/callback`
- **GitHub Webhook Payload URL:**  
  `https://dn.koharu.live/api/webhook/github`

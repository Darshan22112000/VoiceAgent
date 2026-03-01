# 🎙️ Vikara Voice Scheduling Agent

An AI-powered outbound voice agent that calls prospects, qualifies their AI needs, and books discovery sessions via Google Calendar all through a natural voice conversation.

**Maya** (the AI agent) introduces Vikara, qualifies the prospect, collects their details, and sends a Google Calendar invite without any manual intervention.

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Angular 18 |
| Backend | FastAPI (Python) |
| Voice AI | VAPI (Deepgram STT + GPT-4o + ElevenLabs TTS) |
| Calendar | Google Calendar API |
| Deployment | Railway (backend + frontend) |



## 🚀 Using the Deployed App

### Step 1 — Open the App

Visit your deployed frontend URL (e.g. `https://hospitable-passion-production-3c07.up.railway.app/`).

### Step 2 — Sign In With Google to Authenticate

Click **Connect Google Calendar** → sign in with your Google account → Logged In.

> Note: This is used to identify you. Calendar invites are always sent from the configured host email.

### Step 3 — Start a Call

Click **Start Outbound Call**. Maya will greet you and begin the conversation.

### Step 4 — Have a Conversation

Maya will:
1. Introduce Vikara and ask if you're exploring AI
2. Qualify your needs
3. Collect your name, phone, email, preferred date & time
4. Read everything back for confirmation
5. Book the session and send a Google Calendar invite

### Step 5 — Check Your Email

You'll receive a Google Calendar invite at the email you provided during the call.

---

## 🛠️ Running Locally

### 1. Clone the Repository

```bash
git clone https://github.com/Darshan22112000/VoiceAgent.git
cd VoiceAgent
```

---

## 📋 Prerequisites

Before you begin, you'll need accounts and API keys from:

- [VAPI](https://vapi.ai) — voice AI platform
- [Google Cloud Console](https://console.cloud.google.com) — for OAuth + Calendar API
- [ElevenLabs](https://elevenlabs.io) — for Maya's voice (via VAPI)
- [Railway](https://railway.app) — for deployment
- [ngrok](https://ngrok.com) — for local development only

---

### 2. Backend Setup

#### Install Python dependencies

```bash
cd server
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

#### Create `.env` file

```bash
cp .env.example .env
```

Fill in all values (see **Environment Variables** section below).

#### Start ngrok (required for VAPI tool callbacks)

```bash
ngrok http 8000
```

Copy the `https://` URL → set as `BACKEND_URL` in `.env`.

#### Run the backend

```bash
uvicorn app.main:app --reload --port 8000
```

Backend available at `http://localhost:8000`
API docs at `http://localhost:8000/docs`

---

### 3. Frontend Setup

#### Install dependencies

```bash
cd frontend/voice-scheduling-agent-frontend
npm install
```

#### Configure environment

Edit `src/assets/env.js`:

```javascript
(function(window) {
  window.__env = {
    API_URL: 'http://localhost:8000',
    VAPI_PUBLIC_KEY: 'your_vapi_public_key_here'
  };
}(window));
```

#### Run the frontend

```bash
ng serve
```

Frontend available at `http://localhost:4200`

---

### 4. Google Cloud Setup

#### Create OAuth Credentials

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project (or use existing)
3. Go to **APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID**
4. Application type: **Web application**
5. Add authorized redirect URIs:
   - `http://localhost:8000/auth/callback` (local)
   - `https://your-backend.railway.app/auth/callback` (production)
6. Copy `Client ID` and `Client Secret` to `.env`

#### Enable APIs

Go to **APIs & Services → Enable APIs and Services** and enable:
- Google Calendar API
- Gmail API
- Google OAuth2 API

#### OAuth Consent Screen

Go to **APIs & Services → OAuth consent screen**:
- Add scopes: `calendar`, `gmail`, `userinfo.email`, `userinfo.profile`
- Add test users (your email) while in testing mode
- Publish app when ready for production

---

### 5. VAPI Setup

1. Sign up at [vapi.ai](https://vapi.ai)
2. Go to **Dashboard → API Keys**
3. Copy your **Private Key** → `VAPI_API_KEY` in `.env`
4. Copy your **Public Key** → `VAPI_API_PUBLIC_KEY` in `.env` and `env.js`
5. Create an assistant via the API:

```bash
POST http://localhost:8000/assistant/refresh
```

Copy the returned `assistant_id` → set as `VAPI_ASSISTANT_ID` in `.env`

---

### 6. Google Calendar Refresh Token

This allows the app to always send calendar invites from your email:

1. Make sure `GOOGLE_SCOPES` includes `calendar` and `gmail` scopes
2. Start the backend and login with Google at `http://localhost:4200`
3. After login, hit:

```bash
GET http://localhost:8000/auth/my-token
```

4. Copy the `refresh_token` value → set as `GOOGLE_CALENDAR_REFRESH_TOKEN` in `.env`

---

## 🔑 Environment Variables

Create `server/.env` with the following:

```bash
# ── VAPI ──────────────────────────────────────────
VAPI_API_KEY=your_private_key              # Private key (backend only)
VAPI_API_PUBLIC_KEY=your_public_key        # Public key (also in frontend env.js)
VAPI_ASSISTANT_ID=uuid-of-your-assistant   # From /assistant/refresh endpoint

# ── Google OAuth ───────────────────────────────────
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback

# ── Google Calendar ────────────────────────────────
GOOGLE_CALENDAR_REFRESH_TOKEN=your_refresh_token   # From /auth/my-token endpoint
YOUR_EMAIL=your-email@gmail.com                     # All invites sent from this email

# ── App Config ─────────────────────────────────────
BACKEND_URL=https://your-ngrok-url.ngrok.io        # Public URL for VAPI callbacks
FRONTEND_URL=http://localhost:4200
ENVIRONMENT=development
DEFAULT_TIMEZONE=America/Los_Angeles
ASSISTANT_NAME=Maya
CORS_ORIGINS=http://localhost:4200

# ── Optional ───────────────────────────────────────
LOG_LEVEL=INFO
```

---

## ☁️ Deploying to Railway

### Backend

1. Go to [railway.app](https://railway.app) → **New Project → Deploy from GitHub**
2. Select your repo → set **Root Directory** to `server`
3. Add all environment variables from above (update URLs to production values)
4. After deployment, update:
   - `BACKEND_URL` → your Railway backend URL
   - `GOOGLE_REDIRECT_URI` → `https://your-backend.railway.app/auth/callback`
5. Add redirect URI in Google Cloud Console

### Frontend

1. In the same Railway project → **New Service → GitHub repo**
2. Set **Root Directory** to `frontend/voice-scheduling-agent-frontend`
3. Add environment variables:

```
API_URL=https://your-backend.railway.app
VAPI_PUBLIC_KEY=your_vapi_public_key
NIXPACKS_NODE_VERSION=22
PORT=3000
```

### Post-Deployment

1. Update `CORS_ORIGINS` in backend to include your frontend Railway URL
2. Refresh VAPI assistant with production URL:

```bash
POST https://your-backend.railway.app/assistant/refresh
```

3. Update `VAPI_ASSISTANT_ID` in Railway backend variables with the new ID

---

## 📁 Project Structure

```
VoiceAgent/
├── server/
│   ├── app/
│   │   ├── main.py          # FastAPI app, all routes and endpoints
│   │   ├── config.py        # Environment config + VAPI assistant config
│   │   └── models.py        # Pydantic models
│   ├── requirements.txt
│   ├── Procfile
│   └── railway.toml
│
└── frontend/
    └── voice-scheduling-agent-frontend/
        ├── src/
        │   ├── app/
        │   │   ├── app.component.ts    # Main Angular component
        │   │   ├── app.component.html  # UI template
        │   │   └── app.component.scss  # Dark theme styles
        │   ├── assets/
        │   │   ├── env.js              # Runtime config (local dev)
        │   │   └── env.template.js     # Runtime config (production)
        │   └── environments/
        │       ├── environment.ts
        │       └── environment.prod.ts
        ├── Dockerfile
        ├── start.sh
        └── railway.toml
```

---

## 🔄 Key API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/auth/google` | Start Google OAuth flow |
| `GET` | `/auth/callback` | Google OAuth callback |
| `GET` | `/auth/status` | Check if authenticated |
| `POST` | `/auth/logout` | Logout |
| `POST` | `/call/start` | Start a VAPI web call |
| `POST` | `/vapi/tool/book-appointment` | VAPI tool callback — books calendar event |
| `POST` | `/vapi/webhook` | VAPI lifecycle events |
| `POST` | `/assistant/refresh` | Create/refresh VAPI assistant |
| `GET` | `/appointments` | List all booked appointments |


## 📞 Support

- Website: [vikara.ai](https://vikara.ai)
- Email: ask@vikara.ai
- Phone: +1 510 309 6846
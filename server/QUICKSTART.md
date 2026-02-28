# 🚀 Quick Start Guide - Voice Scheduling Agent

## Prerequisites

- Python 3.8+
- Virtual environment `venv_voice` (already created)
- Dependencies installed (already done with `requirements.txt`)

---

## Step 1: Configure Environment Variables

### 1.1 Copy the template:
```bash
cp .env.example .env
```

### 1.2 Edit `.env` with your actual values:
```env
# Required for VAPI
VAPI_API_KEY=your_vapi_private_key
VAPI_API_PUBLIC_KEY=your_vapi_public_key
VAPI_ASSISTANT_ID=your_assistant_id_or_leave_empty

# Required for Google Calendar
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback

# Your business email
YOUR_EMAIL=your.email@company.com

# Optional but recommended
ENVIRONMENT=development
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:4200
ASSISTANT_NAME=Maya
DEFAULT_TIMEZONE=America/Los_Angeles
LOG_LEVEL=INFO
```

---

## Step 2: Activate Virtual Environment

### Windows (PowerShell):
```powershell
cd C:\Users\Darshan Vetal\Desktop\Learning\AI\voice_agent\server
.\venv_voice\Scripts\Activate.ps1
```

### macOS/Linux:
```bash
source venv_voice/bin/activate
```

---

## Step 3: Run the Application

### Development Mode (with auto-reload):
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Expected Output:
```
INFO:     Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## Step 4: Test the API

### Health Check:
```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy", "timestamp": "2026-02-28T..."}
```

### Start Google Auth:
```bash
curl http://localhost:8000/auth/google
# Returns: {"auth_url": "https://accounts.google.com/o/oauth2/auth?..."}
```

### Book an Appointment (with API key):
```bash
curl -X POST http://localhost:8000/vapi/tool/book-appointment \
  -H "X-API-Key: YOUR_VAPI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "phone": "+1-555-123-4567",
    "email": "john@example.com",
    "date": "2026-03-15",
    "time": "14:00",
    "purpose": "AI Transformation Discussion",
    "timezone": "America/Los_Angeles",
    "duration_minutes": 60
  }'
# Expected: {"result": "Booked! Calendar invite sent...", "success": true, ...}
```

---

## Step 5: API Key Configuration

### For VAPI Webhook Calls:

When VAPI calls your `/vapi/tool/book-appointment` endpoint, it must include:

```bash
X-API-Key: YOUR_VAPI_API_KEY
```

**Set in VAPI Dashboard:**
1. Go to your VAPI Assistant
2. In the Tools section, set the Custom Tool URL to:
   ```
   http://your-backend-url/vapi/tool/book-appointment
   ```
3. Add header authentication:
   ```
   X-API-Key: your_vapi_api_key
   ```

---

## Endpoints Overview

### Public Endpoints:
- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /auth/google` - Initiate Google OAuth
- `GET /auth/callback?code=...` - Google OAuth callback
- `GET /auth/status` - Check if authenticated
- `POST /auth/logout` - Logout
- `POST /call/start` - Start web call with VAPI
- `POST /call/start_phone` - Start phone call with VAPI

### Protected Endpoints (Require X-API-Key):
- `POST /vapi/tool/book-appointment` - Book appointment (calls from VAPI)

### Webhook Endpoints:
- `POST /vapi/webhook` - Receive VAPI lifecycle events

### Data Endpoints:
- `GET /appointments` - List all booked appointments (for reference only)

---

## Security Features (Now Implemented)

✅ **API Key Validation**
- `/vapi/tool/book-appointment` requires `X-API-Key` header
- Prevents unauthorized appointment bookings

✅ **Input Validation**
- Email format validation
- Phone format validation (10-20 chars, digits/spaces/hyphens/+)
- Date validation (future dates only, YYYY-MM-DD format)
- Time validation (24-hour format HH:MM)
- Timezone validation (IANA timezone strings)
- Duration constraints (15-480 minutes)

✅ **Configuration Management**
- All secrets in `.env` file
- Environment-based configuration
- No hardcoded credentials

✅ **Error Handling**
- Proper error messages for validation failures
- Google Calendar-specific error handling
- Structured logging

⚠️ **Still TODO (Phase 2):**
- [ ] Database for persistent storage
- [ ] JWT authentication for user management
- [ ] Rate limiting on public endpoints
- [ ] Token encryption at rest
- [ ] VAPI webhook signature verification

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'app'"
**Solution:**
- Make sure you're in the `server` directory
- Ensure `venv_voice` is activated
- Check that `app/__init__.py` exists

### Issue: "YOUR_EMAIL not configured"
**Solution:**
- Add `YOUR_EMAIL=your@email.com` to `.env`
- The app validates this on startup

### Issue: "Invalid API key" when booking
**Solution:**
- Check that `X-API-Key` header matches `VAPI_API_KEY` in `.env`
- VAPI needs to send this header in request to `/vapi/tool/book-appointment`

### Issue: "Invalid timezone" error
**Solution:**
- Use IANA timezone format: `America/Los_Angeles`, `Europe/London`, `Asia/Tokyo`
- See full list: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

### Issue: Google Calendar integration not working
**Solution:**
- Complete the Google OAuth flow by visiting `/auth/google`
- Follow the redirect to authenticate
- Ensure `GOOGLE_REDIRECT_URI` matches Google Cloud Console settings

---

## Environment Variables Reference

| Variable | Type | Required | Example | Notes |
|----------|------|----------|---------|-------|
| `ENVIRONMENT` | string | No | `development` | Set to `production` for production |
| `VAPI_API_KEY` | secret | Yes | `sk_...` | Private API key for VAPI |
| `VAPI_API_PUBLIC_KEY` | secret | Yes | `pk_...` | Public key for browser calls |
| `VAPI_ASSISTANT_ID` | string | No | `uuid-...` | Leave empty to create new assistant |
| `GOOGLE_CLIENT_ID` | secret | Yes | `xxx.apps...` | From Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | secret | Yes | `GOCSPX...` | From Google Cloud Console |
| `GOOGLE_REDIRECT_URI` | string | Yes | `http://localhost:8000/auth/callback` | Must match Cloud Console |
| `YOUR_EMAIL` | string | Yes | `user@company.com` | Your Gmail/business email |
| `ASSISTANT_NAME` | string | No | `Maya` | Name of AI voice assistant |
| `DEFAULT_TIMEZONE` | string | No | `America/Los_Angeles` | Default timezone for bookings |
| `BACKEND_URL` | string | Yes | `http://localhost:8000` | Your backend URL |
| `FRONTEND_URL` | string | No | `http://localhost:4200` | Frontend URL for CORS |
| `SECRET_KEY` | secret | No* | `min_32_chars...` | * Required if using JWT auth |
| `LOG_LEVEL` | string | No | `INFO` | DEBUG, INFO, WARNING, ERROR |
| `CORS_ORIGINS` | string | No | `http://localhost:4200` | Comma-separated list |

---

## Development Tips

### Enable Debug Logging:
```bash
# Set in .env
LOG_LEVEL=DEBUG
```

### View Database/In-Memory Appointments:
```bash
curl http://localhost:8000/appointments
```

### Test Input Validation Errors:
```bash
# Invalid email
curl -X POST http://localhost:8000/vapi/tool/book-appointment \
  -H "X-API-Key: test_key" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "phone": "555-1234", "email": "invalid", "date": "2026-03-15", "time": "14:00", "purpose": "Test"}'

# Past date
curl -X POST http://localhost:8000/vapi/tool/book-appointment \
  -H "X-API-Key: test_key" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "phone": "555-1234", "email": "test@example.com", "date": "2020-03-15", "time": "14:00", "purpose": "Test"}'

# Missing required field
curl -X POST http://localhost:8000/vapi/tool/book-appointment \
  -H "X-API-Key: test_key" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test"}'
```

---

## Next Steps

### Phase 2 - Database & Persistence:
1. Set up PostgreSQL or SQLite
2. Create database models with SQLAlchemy
3. Migrate token storage to database
4. Add token encryption

### Phase 2 - Authentication:
1. Implement JWT authentication
2. Add `/auth/register` and `/auth/login` endpoints
3. Create protected routes for authenticated users

### Phase 2 - Advanced Security:
1. Add rate limiting with `slowapi`
2. Implement VAPI webhook signature verification
3. Add comprehensive audit logging

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review application logs (set `LOG_LEVEL=DEBUG`)
3. Check `.env` configuration
4. Verify VAPI and Google Cloud Console settings

---

**Version:** 1.0.0  
**Last Updated:** February 28, 2026  
**Status:** Phase 1 Security Fixes Complete ✅


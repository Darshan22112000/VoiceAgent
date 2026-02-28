# Email Sending Solution - YOUR_EMAIL vs Authenticated Account

## The Problem

You want calendar invites to be sent FROM `YOUR_EMAIL`, but currently they're being sent from the authenticated user's email.

## The Root Cause

**Google Calendar API Limitation:** Calendar invites are ALWAYS sent from the authenticated user's email account. There is no API parameter to change this.

```
Authenticated User Email: user@example.com
YOUR_EMAIL (desired sender): boss@company.com
├─ Event created in: boss@company.com calendar ✅
└─ Email sent FROM: user@example.com ❌ (Not what we want)
```

## The Solution

**Authenticate with YOUR_EMAIL Account**

The invites will automatically be sent from `YOUR_EMAIL` if you authenticate with that account.

### Step-by-Step Instructions:

#### 1. Go to the Auth Endpoint
```
http://localhost:8000/auth/google
```

#### 2. Login with YOUR_EMAIL Account
When prompted, sign in with:
- Email: `YOUR_EMAIL` (from .env)
- Password: Your Google password

#### 3. Grant Permissions
Click "Allow" to grant Calendar access

#### 4. From Now On
- Calendar invites will be sent FROM `YOUR_EMAIL` ✅
- Organizer will be `YOUR_EMAIL` ✅
- Attendees will receive invites from your email ✅

---

## How It Works

### Before (Wrong Auth)
```
OAuth Authentication: authenticated@example.com
YOUR_EMAIL in .env: boss@company.com

Result:
├─ Event organizer shown: boss@company.com ✅
└─ Email sent from: authenticated@example.com ❌
```

### After (Correct Auth)
```
OAuth Authentication: boss@company.com  ← Same as YOUR_EMAIL
YOUR_EMAIL in .env: boss@company.com

Result:
├─ Event organizer shown: boss@company.com ✅
└─ Email sent from: boss@company.com ✅
```

---

## Code Changes Made

### In `app/main.py`

Added clarifying comments at the top:
```python
# ────────────────────────────────────────────────────────────────────────────────
# IMPORTANT: Email Sending & Authentication
# ────────────────────────────────────────────────────────────────────────────────
# Google Calendar API sends invites from the AUTHENTICATED account's email.
#
# To send invites FROM YOUR_EMAIL:
#   ✅ Make sure you authenticate with the YOUR_EMAIL account via OAuth
#   ✅ Go to /auth/google and login with YOUR_EMAIL account
#   ✅ Then calendar invites will be sent from YOUR_EMAIL
#
# If invites are coming from a different email:
#   🔴 You authenticated with a different account
#   🔴 Re-authenticate with YOUR_EMAIL account via /auth/google
# ────────────────────────────────────────────────────────────────────────────────
```

Updated the `create_google_calendar_event()` function docstring:
```python
def create_google_calendar_event(appt: AppointmentDetails) -> dict:
    """Create a Google Calendar event with validated appointment details.
    
    IMPORTANT: For emails to appear from YOUR_EMAIL, you must authenticate
    with the YOUR_EMAIL account via OAuth. The calendar invite will always
    be sent from the authenticated account's email address.
    """
```

Added logging to show what's happening:
```python
logger.info(f"✅ Event created: {created.get('id')} | Calendar invite sent to {appt.email}")
logger.info(f"   Event organizer: {YOUR_EMAIL} | Email sent from: authenticated account")
```

---

## Verification Checklist

### To verify emails are coming from YOUR_EMAIL:

- [ ] Go to `/auth/google` endpoint
- [ ] Login with YOUR_EMAIL account (the one you want invites from)
- [ ] Check that `YOUR_EMAIL` matches the login email
- [ ] Create a test appointment booking
- [ ] Check the email received by the customer
- [ ] Verify "From" address is YOUR_EMAIL
- [ ] Verify "Organizer" is YOUR_EMAIL

---

## Technical Details

### The Issue in Google Calendar API

```python
created = service.events().insert(
    calendarId="primary",
    body=event_body,
    sendUpdates="all"  # ← This sends from authenticated user's account
).execute()
```

The `sendUpdates="all"` parameter:
- ✅ Automatically sends calendar invites
- ❌ Always sends FROM the authenticated user's email
- ❌ No way to specify a different sender email

### Why This is By Design

Google Calendar API sends invites through the authenticated user's email for security reasons:
- Prevents email spoofing
- Ensures only authorized users can send invites
- Maintains email authenticity

---

## Alternative Solutions (If Needed)

### Option 1: Gmail API for Custom Emails (Advanced)
If you need more control over the email format, we could:
1. Create the event with `sendUpdates="externalOnly"`
2. Send a custom email using Gmail API
3. Total effort: 2-3 hours

### Option 2: Delegate Calendar Access (Advanced)
Set up calendar delegation so multiple accounts can send from YOUR_EMAIL:
1. Requires additional Google Workspace setup
2. More complex configuration
3. Not recommended for this use case

### Option 3: Use Service Account (Advanced)
- Create a Google Service Account
- More complex authentication flow
- Better for server-to-server scenarios
- Total effort: 4-6 hours

---

## FAQ

### Q: Why aren't the emails coming from YOUR_EMAIL?
**A:** You authenticated with a different Google account via OAuth. Go to `/auth/google` and login with YOUR_EMAIL.

### Q: Can I change the sender without re-authenticating?
**A:** No. Google Calendar API sends from the authenticated account. You must authenticate with the email you want to send from.

### Q: What if I don't want to authenticate again?
**A:** That's fine! The event will still be created and the customer will get an invite. It will just come from a different email address.

### Q: Can I send from multiple email addresses?
**A:** To send from different emails, you'd need to:
1. Authenticate with Email A (invites come from Email A)
2. Authenticate with Email B (invites come from Email B)
3. This requires storing multiple authentication tokens (Phase 2 Database task)

### Q: Why does the `organizer` field show YOUR_EMAIL but the email is from someone else?
**A:** The "organizer" is the calendar event owner (YOUR_EMAIL). The "sender" is the authenticated user's email. They're different fields.

---

## Testing

### Test 1: Verify Current Behavior
```bash
# 1. Check current authentication
curl http://localhost:8000/auth/status
# Returns: {"authenticated": true/false}

# 2. Check who's authenticated
curl http://localhost:8000/auth/google
# This shows the login prompt
```

### Test 2: Re-authenticate
```bash
# 1. Logout first
curl -X POST http://localhost:8000/auth/logout

# 2. Go to /auth/google in browser
# 3. Login with YOUR_EMAIL account
# 4. Grant permissions
# 5. You're now authenticated as YOUR_EMAIL
```

### Test 3: Create Appointment
```bash
# This will now send the invite FROM YOUR_EMAIL
curl -X POST http://localhost:8000/vapi/tool/book-appointment \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Client",
    "email": "client@example.com",
    "phone": "555-1234",
    "date": "2026-03-15",
    "time": "14:00",
    "purpose": "Test",
    "timezone": "America/Los_Angeles",
    "duration_minutes": 60
  }'

# Check the email received by client@example.com
# The "From" address should now be YOUR_EMAIL
```

---

## Summary

**The Fix:** Authenticate with `YOUR_EMAIL` account via OAuth at `/auth/google`

**Result:** Calendar invites will automatically be sent from `YOUR_EMAIL`

**Time to implement:** 2 minutes (just re-authenticate)

**Complexity:** None - just use the existing auth flow with the correct account

---

**Code is ready. Just re-authenticate with YOUR_EMAIL and emails will come from that address!** ✅


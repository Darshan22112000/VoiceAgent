import os

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
import httpx
import json
from datetime import datetime, timedelta
import pytz
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging

from pydantic import BaseModel

# Import configuration and models
from app.config import (
    VAPI_API_KEY, VAPI_API_PUBLIC_KEY, VAPI_ASSISTANT_ID,
    GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI,
    BACKEND_URL, FRONTEND_URL, GOOGLE_SCOPES, YOUR_EMAIL, 
    DEFAULT_TIMEZONE, ASSISTANT_NAME, LOG_LEVEL, CORS_ORIGINS, build_assistant_config
)
from app.models import AppointmentDetails, CallResponse

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(title="Voice Scheduling Agent API", version="1.0.0")

# Configure CORS properly
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory stores - TODO: Replace with database (PostgreSQL/MongoDB)
# This is temporary for MVP. Production should use persistent storage
token_store    = {}   # Google OAuth tokens
booked_slots   = []   # All booked appointments (for reference)



# ── Google OAuth ──────────────────────────────────────────────────────────────
def get_google_flow():
    client_config = {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uris": [GOOGLE_REDIRECT_URI],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    flow = Flow.from_client_config(client_config, scopes=GOOGLE_SCOPES)
    flow.redirect_uri = GOOGLE_REDIRECT_URI
    return flow


def get_calendar_service():
    if "default" not in token_store:
        raise HTTPException(status_code=401, detail="Google Calendar not connected. Please authenticate first.")
    creds = Credentials(**token_store["default"])
    return build("calendar", "v3", credentials=creds)


# ── Calendar Helper ───────────────────────────────────────────────────────────
def create_google_calendar_event(appt: AppointmentDetails) -> dict:
    """Create a Google Calendar event with validated appointment details.

    IMPORTANT: For emails to appear from YOUR_EMAIL, you must authenticate
    with the YOUR_EMAIL account via OAuth. The calendar invite will always
    be sent from the authenticated account's email address.
    """
    try:
        service = get_calendar_service()
        tz = pytz.timezone(appt.timezone)

        dt_str   = f"{appt.date}T{appt.time}:00"
        start_dt = tz.localize(datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S"))
        end_dt   = start_dt + timedelta(minutes=appt.duration_minutes)

        event_body = {
            "summary": f"Vikara Discovery Session — {appt.name}",
            "description": (
                f"Free Discovery Session with Vikara\n"
                f"vikara.ai | ask@vikara.ai | +1 510 309 6846\n\n"
                f"Client:   {appt.name}\n"
                f"Phone:    {appt.phone}\n"
                f"Email:    {appt.email}\n"
                f"Session:  {appt.purpose}\n\n"
                f"Offices: SF Bay Area · Bengaluru · Melbourne"
            ),
            "start": {
                "dateTime": start_dt.isoformat(),
                "timeZone": appt.timezone,
            },
            "end": {
                "dateTime": end_dt.isoformat(),
                "timeZone": appt.timezone,
            },
            "organizer": {
                "email":       YOUR_EMAIL,
                "displayName": "Vikara Team",
                "self":        True,
            },
            "attendees": [
                {
                    "email":          YOUR_EMAIL,
                    "displayName":    "Vikara Team",
                    "organizer":      True,
                    "responseStatus": "accepted",
                },
                {
                    "email":          appt.email,
                    "displayName":    appt.name,
                    "responseStatus": "needsAction",
                },
            ],
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email",  "minutes": 24 * 60},
                    {"method": "email",  "minutes": 60},
                    {"method": "popup",  "minutes": 30},
                ],
            },
            "guestsCanSeeOtherGuests": False,
        }

        # Create event - email will be sent FROM the authenticated user's account
        # To send from YOUR_EMAIL, authenticate with that account via OAuth
        created = service.events().insert(
            calendarId  = "primary",
            body        = event_body,
            sendUpdates = "all",  # This sends from authenticated user's account
        ).execute()

        logger.info(f"✅ Event created: {created.get('id')} | Calendar invite sent to {appt.email}")
        logger.info(f"   Event organizer: {YOUR_EMAIL} | Email sent from: authenticated account")

        booked_slots.append({
            "event_id":   created.get("id"),
            "name":       appt.name,
            "email":      appt.email,
            "phone":      appt.phone,
            "date":       appt.date,
            "time":       appt.time,
            "purpose":    appt.purpose,
            "event_link": created.get("htmlLink"),
            "created_at": datetime.utcnow().isoformat(),
        })

        return {
            "success":    True,
            "event_id":   created.get("id"),
            "event_link": created.get("htmlLink"),
            "start":      start_dt.isoformat(),
            "end":        end_dt.isoformat(),
        }

    except HttpError as e:
        logger.error(f"Google Calendar error: {e}")
        # Return user-friendly error instead of raising
        if "403" in str(e):
            return {"success": False, "error": "Calendar permission denied. Please re-authenticate."}
        elif "409" in str(e):
            return {"success": False, "error": "Time slot conflict detected."}
        raise HTTPException(status_code=500, detail=f"Calendar error: {str(e)}")

# ─────────────────────────────────────────────────────────────────────────────
#  ROUTES
# ─────────────────────────────────────────────────────────────────────────────
# Add this new model near your other models at the top
class ToolCallFunction(BaseModel):
    name: str
    arguments: dict | str  # VAPI sometimes sends as string

class ToolCall(BaseModel):
    function: ToolCallFunction

class VapiToolRequest(BaseModel):
    toolCall: ToolCall


@app.get("/")
async def root():
    return {"message": "Voice Scheduling Agent API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# ── Google Auth ───────────────────────────────────────────────────────────────
@app.get("/auth/google")
async def google_auth():
    flow    = get_google_flow()
    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
    return {"auth_url": auth_url}


@app.get("/auth/callback")
async def google_callback(code: str):
    try:
        flow = get_google_flow()
        flow.fetch_token(code=code)
        creds = flow.credentials
        token_store["default"] = {
            "token":         creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri":     creds.token_uri,
            "client_id":     creds.client_id,
            "client_secret": creds.client_secret,
            "scopes":        list(creds.scopes),
        }
        # Redirect back to frontend after auth
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=os.getenv("FRONTEND_URL", "http://localhost:4200"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/auth/status")
async def auth_status():
    return {"authenticated": "default" in token_store}


# ── START CALL (called by Angular button) ─────────────────────────────────────
@app.post("/call/start_phone")
async def start_phone_call():
    if not VAPI_API_PUBLIC_KEY:
        raise HTTPException(status_code=500, detail="VAPI_API_PUBLIC_KEY not configured")

    assistant_config = build_assistant_config()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.vapi.ai/call",
                headers={
                    "Authorization": f"Bearer {VAPI_API_PUBLIC_KEY}",
                    "Content-Type":  "application/json",
                },
                json={
                    "type":      "outboundPhoneCall",      # ✅ correct type for browser calls
                    "assistant": assistant_config,
                },
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            logger.info(f"VAPI call created: {data.get('id')}")

            return {
                "call_id":      data.get("id"),
                "web_call_url": data.get("webCallUrl"),
            }

    except httpx.HTTPStatusError as e:
        logger.error(f"VAPI API error: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error(f"Error starting call: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/call/start")
async def start_call():
    if not VAPI_API_KEY:
        raise HTTPException(status_code=500, detail="VAPI_API_KEY not configured")

    assistant_config = build_assistant_config()

    try:
        async with httpx.AsyncClient() as client:

            # ── Step 1: Create a temporary assistant, get its UUID ──────────
            # ── Step 1: Always update assistant config ──────────────────────
            if VAPI_ASSISTANT_ID:
                # ✅ PATCH existing assistant with latest config
                assistant_response = await client.patch(
                    f"https://api.vapi.ai/assistant/{VAPI_ASSISTANT_ID}",
                    headers={
                        "Authorization": f"Bearer {VAPI_API_KEY}",  # ✅ private key
                        "Content-Type": "application/json",
                    },
                    json=assistant_config,
                    timeout=60.0,
                )
                assistant_response.raise_for_status()
                assistant_id = VAPI_ASSISTANT_ID
                logger.info(f"✅ Assistant updated: {assistant_id}")
            else:
                # Create new assistant if no ID in .env
                assistant_response = await client.post(
                    "https://api.vapi.ai/assistant",
                    headers={
                        "Authorization": f"Bearer {VAPI_API_KEY}",  # ✅ private key
                        "Content-Type": "application/json",
                    },
                    json=assistant_config,
                    timeout=60.0,
                )
                assistant_response.raise_for_status()
                assistant_id = assistant_response.json().get("id")
                logger.info(f"✅ Assistant created: {assistant_id}")

            # ── Step 2: Create web call using assistantId ───────────────────
            call_response = await client.post(
                "https://api.vapi.ai/call/web",
                headers={
                    "Authorization": f"Bearer {VAPI_API_PUBLIC_KEY}",
                    "Content-Type":  "application/json",
                },
                json={"assistantId": assistant_id},   # ✅ UUID not inline config
                timeout=60.0,
            )
            call_response.raise_for_status()
            call_data = call_response.json()

            web_call_url = call_data.get("webCallUrl") or call_data.get("transport", {}).get("callUrl")
            logger.info(f"Web call created: {call_data.get('id')} | URL: {web_call_url}")

            return {
                "call_id":      call_data.get("id"),
                "assistant_id": assistant_id,
                "web_call_url": web_call_url,
            }

    except httpx.HTTPStatusError as e:
        logger.error(f"VAPI API error: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error(f"Error starting call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── VAPI TOOL ENDPOINT (VAPI calls this when AI collects all details) ─────────
@app.post("/vapi/tool/book-appointment")
async def book_appointment_tool(request: Request):
    raw_body = await request.body()
    logger.info(f"TOOL CALLED — raw: {raw_body.decode()}")

    try:
        body = json.loads(raw_body)

        # ── Extract toolCallId (VAPI requires this echoed back in response) ──
        tool_call_id = None
        if "message" in body:
            tool_call_list = body["message"].get("toolCallList", [])
            if tool_call_list:
                tool_call_id = tool_call_list[0].get("id")
        if not tool_call_id and "toolCall" in body:
            tool_call_id = body["toolCall"].get("id")
        if not tool_call_id and "toolCallList" in body:
            tool_call_id = body["toolCallList"][0].get("id")

        logger.info(f"toolCallId: {tool_call_id}")

        def vapi_response(message: str):
            """
            VAPI requires this exact shape:
            { "results": [{ "toolCallId": "...", "result": "..." }] }
            Without toolCallId echoed back, VAPI ignores the response
            and falls back to its own error message.
            """
            return {
                "results": [
                    {
                        "toolCallId": tool_call_id,
                        "result": message,
                    }
                ]
            }

        # ── Extract args ──────────────────────────────────────────────────────
        args = None
        if "message" in body:
            tool_call_list = body["message"].get("toolCallList", [])
            if tool_call_list:
                args = tool_call_list[0].get("function", {}).get("arguments")
        if not args and "toolCall" in body:
            args = body["toolCall"].get("function", {}).get("arguments")
        if not args and "toolCallList" in body:
            args = body["toolCallList"][0].get("function", {}).get("arguments")
        if not args and "function" in body:
            args = body["function"].get("arguments")
        if not args and "name" in body and "email" in body:
            args = body

        if not args:
            logger.error(f"Could not extract args. Full body: {json.dumps(body, indent=2)}")
            return vapi_response("I had trouble reading the booking details. Could you try again?")

        # Handle JSON string arguments
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError as e:
                logger.error(f"Malformed JSON in args: {args} — {e}")
                return vapi_response("Invalid data format. Please try again.")

        logger.info(f"Extracted args: {args}")

        # Validate required fields
        missing = [f for f in ["name", "phone", "email", "date", "time"] if not args.get(f)]
        if missing:
            logger.error(f"Missing required fields: {missing}")
            return vapi_response(f"I'm missing {', '.join(missing)}. Could you provide those?")

        appt = AppointmentDetails(
            name             = args.get("name"),
            phone            = args.get("phone"),
            email            = args.get("email"),
            date             = args.get("date"),
            time             = args.get("time"),
            purpose          = args.get("purpose", "Discovery Session"),
            timezone         = args.get("timezone", DEFAULT_TIMEZONE),
            duration_minutes = args.get("duration_minutes", 60),
        )

        logger.info(f"Booking for {appt.name} | {appt.email} | {appt.date} {appt.time}")
        result = create_google_calendar_event(appt)

        if not result.get("success"):
            logger.error(f"Calendar creation failed: {result}")
            return vapi_response(result.get("error", "Failed to create calendar event. Please try again."))

        logger.info(f"✅ Event created: {result.get('event_link')}")
        return vapi_response(f"Your session is booked! A calendar invite has been sent to {appt.email}. We look forward to speaking with you!")

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        error_msg = str(e).lower()
        if "email" in error_msg:
            msg = "Invalid email address. Could you double-check your email?"
        elif "phone" in error_msg:
            msg = "Invalid phone number. Could you provide a valid phone number?"
        elif "date" in error_msg:
            msg = "Invalid date. Please provide a future date."
        elif "time" in error_msg:
            msg = "Invalid time format. Please provide a time like 2pm or 14:00."
        elif "timezone" in error_msg:
            msg = "Invalid timezone. Defaulting to Pacific Time."
        else:
            msg = f"Invalid input: {str(e)}"
        # tool_call_id may not be set yet if error happened before extraction — safe fallback
        return {"results": [{"toolCallId": tool_call_id, "result": msg}]}

    except HTTPException as e:
        logger.error(f"HTTP error in booking: {e.detail}")
        return {"results": [{"toolCallId": tool_call_id, "result": str(e.detail)}]}

    except Exception as e:
        logger.error(f"Booking error: {e}", exc_info=True)
        return {"results": [{"toolCallId": tool_call_id, "result": "Something went wrong on our end. I'll try once more."}]}


# ── VAPI WEBHOOK (lifecycle events) ──────────────────────────────────────────
@app.post("/vapi/webhook")
async def vapi_webhook(request: Request):
    """Receive VAPI lifecycle events — call start, end, transcript, etc."""
    body       = await request.json()
    event_type = body.get("message", {}).get("type", "unknown")
    logger.info(f"VAPI webhook: {event_type}")

    if event_type == "end-of-call-report":
        msg = body.get("message", {})
        logger.info(
            f"Call ended | Duration: {msg.get('durationSeconds')}s | "
            f"Cost: ${msg.get('cost', 0):.4f}"
        )
    return {"received": True}

@app.post("/auth/logout")
async def logout():
    if "default" in token_store:
        del token_store["default"]
    return {"success": True, "message": "Logged out successfully"}

# ── LIST APPOINTMENTS ─────────────────────────────────────────────────────────
@app.get("/appointments")
async def list_appointments():
    """Return all booked appointments."""
    return {"appointments": booked_slots, "count": len(booked_slots)}

@app.post("/assistant/refresh")
async def refresh_assistant():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.vapi.ai/assistant",
            headers={
                "Authorization": f"Bearer {VAPI_API_KEY}",
                "Content-Type": "application/json",
            },
            json=build_assistant_config(),
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        return {
            "assistant_id": data.get("id"),
            "message": f"Copy to Railway env: VAPI_ASSISTANT_ID={data.get('id')}"
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)



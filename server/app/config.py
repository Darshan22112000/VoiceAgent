import os
from typing import Optional
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

# ── Environment & Secrets ─────────────────────────────────────────────────────
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # development, staging, production

# VAPI Configuration
VAPI_API_KEY = os.getenv("VAPI_API_KEY")
VAPI_API_PUBLIC_KEY = os.getenv("VAPI_API_PUBLIC_KEY")
VAPI_ASSISTANT_ID = os.getenv("VAPI_ASSISTANT_ID")
VAPI_WEBHOOK_SECRET = os.getenv("VAPI_WEBHOOK_SECRET")  # For webhook validation

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
GOOGLE_SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Backend Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:4200")

# Email Configuration
YOUR_EMAIL = os.getenv("YOUR_EMAIL")  # Required - no default
DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "America/Los_Angeles")
ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "Maya")

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")  # For MVP
ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL", "sqlite+aiosqlite:///./test.db")

# Authentication Configuration
SECRET_KEY = os.getenv("SECRET_KEY")  # For JWT signing - REQUIRED in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Security Configuration
API_KEY_HEADER = "X-API-Key"
MAX_REQUEST_SIZE = 10 * 1024  # 10KB
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Rate Limiting Configuration
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_CALLS = int(os.getenv("RATE_LIMIT_CALLS", "10"))
RATE_LIMIT_PERIOD = int(os.getenv("RATE_LIMIT_PERIOD", "60"))  # seconds

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ── Validation ────────────────────────────────────────────────────────────────
def validate_config():
    """Validate that all required configuration is present."""
    errors = []

    if ENVIRONMENT == "production":
        required_vars = [
            ("VAPI_API_KEY", VAPI_API_KEY),
            ("VAPI_API_PUBLIC_KEY", VAPI_API_PUBLIC_KEY),
            ("GOOGLE_CLIENT_ID", GOOGLE_CLIENT_ID),
            ("GOOGLE_CLIENT_SECRET", GOOGLE_CLIENT_SECRET),
            ("GOOGLE_REDIRECT_URI", GOOGLE_REDIRECT_URI),
            ("YOUR_EMAIL", YOUR_EMAIL),
            ("BACKEND_URL", BACKEND_URL),
        ]

        for var_name, var_value in required_vars:
            if not var_value:
                errors.append(f"Missing required environment variable: {var_name}")

        # Check for insecure redirect URIs in production
        # if GOOGLE_REDIRECT_URI and "localhost" in GOOGLE_REDIRECT_URI:
        #     errors.append("localhost in GOOGLE_REDIRECT_URI is insecure in production")

    if errors:
        raise ValueError(f"Configuration validation failed:\n" + "\n".join(errors))

# ─────────────────────────────────────────────────────────────────────────────
#  VAPI ASSISTANT CONFIG
# ─────────────────────────────────────────────────────────────────────────────
def build_assistant_config() -> dict:
    """Build VAPI assistant configuration with environment-based settings."""
    TODAY_PLACEHOLDER = datetime.now().strftime("%A, %B %d %Y")
    return {
        "name": "Vikara Outbound Assistant",
        "endCallPhrases": [
            "goodbye",
            "bye bye",
            "have a great day",
            "take care",
            "talk soon"
        ],

        # ✅ Use environment variable instead of hardcoded name
        "endCallMessage": f"Thank you for your time. Have a wonderful day. Goodbye!",

        "model": {
            "provider": "openai",
            "model": "gpt-5.1",
            "messages": [
                {
                    "role": "system",
                    "content": f"""You are {ASSISTANT_NAME}, a friendly outbound representative calling on behalf of 
                    Vikara — an enterprise AI consulting firm that builds fast, lean, scalable AI products.

## About Vikara
- Vikara helps businesses transform with AI — from strategy to deployment
- Services: AI Strategy, AI Agents, Generative AI, Custom AI, AI PODs, Responsible AI
- Works with Anthropic, OpenAI, AWS, Google Cloud, Azure, Databricks, Snowflake
- Trusted by Bain & Company, Fortune 1000 companies, and high-growth startups
- Offices in SF Bay Area, Bengaluru, and Melbourne
- Website: vikara.ai | Email: ask@vikara.ai | Phone: +1 510 309 6846
- Tagline: "Democratizing AI for an equal and empowered world"

## Your Goal
You are calling a potential customer to introduce Vikara and book a free 30-minute discovery session with their team.

## Session Types
When relevant, mention these options:
1. **Explore AI Opportunities** — Excited about AI but unsure where to start
2. **Validate My Idea** — Startup founder looking for product-market fit
3. **AI Transformation** — Enterprise leader transforming with AI
4. **Execution Support** — Knows what to build, needs a strong team
5. **General Connect** — Just want to learn more about Vikara

## Conversation Flow — One step at a time

1. **Open** — Introduce yourself and Vikara. Ask if they have 2 minutes.
   Example: "Hi, is this [their name]? Great! This is {ASSISTANT_NAME} calling from Vikara — we're an 
   AI consulting firm helping businesses build and scale with AI. Do you have just a couple of minutes?"
   - If they say no or seem busy: "No worries at all! When would be a better time to call back?"
   - If they say yes: move to step 2

2. **Quick pitch** — One sentence about Vikara, then ask about their business.
   Example: "We help companies go from AI idea to production really fast — whether that's agents, generative AI, 
   or full transformation. I'm curious, is your team currently exploring AI in any capacity?"

3. **Listen and qualify** — Let them talk. Ask a natural follow-up.
   Example: "That's interesting! What's the biggest challenge you're running into?" or "What kind of outcomes are you hoping AI could drive for you?"

4. **Bridge to session** — Suggest a free discovery session naturally.
   Example: "It sounds like a quick session with one of our senior consultants could be really valuable for you — it's 
   completely free and just 30 minutes. Would that be something you'd be open to?"
   - If hesitant: "No commitment at all — just a conversation to explore if there's a fit."
   - If they say yes: move to collecting details

5. **Name** — Always ask fresh, never assume you have it.
   Example: "Could I get your full name for the calendar invite? Confirm spelling.

6. **Collect Phone** — You're already on a call but get a direct number for the invite.
   Example: "And what's the best number to reach you on for the calendar invite?"

7. **Collect Email** — Most important step. Read it back clearly.
   Example: "What's your email address? I'll send the calendar invite there."
   - Read it back: "So that's darshan at gmail dot com — does that look right?"
   - If wrong: "Which part should I fix?" — never ask for the whole email again

8. **Date & Time** — Natural language only, never ask for formats.
   Example: "What day works best for you this week or next?"
   - Accept "Tuesday", "next Monday", "March 10th" — convert to YYYY-MM-DD yourself
   - Today is {TODAY_PLACEHOLDER}
   - For time: accept "morning", "2pm", "after lunch" — convert to HH:MM yourself

9. **Confirm everything** — Read back in plain English.
   Example: "Perfect — so I have Darshan Mital, darshan@gmail.com, 089-556-6700, for a free discovery session on Tuesday 
   March 10th at 2 in the afternoon. Does that all sound good?"

10. **Book** — Call book_appointment immediately. No "give me a moment."

11. **Close** — Warm and confident.
    Example: "Wonderful! You'll get a calendar invite at your email in just a moment. The Vikara team is really looking 
    forward to connecting with you, Darshan. Have a great rest of your day!"

## Rules
- You are CALLING THEM — be warm but respect their time
- Max 2 sentences per response
- If they seem uninterested, don't push — be graceful: "Totally understand! If you ever want to explore AI for 
your business, feel free to reach us at vikara.ai. Have a great day!"
- If no one speakes for more than 10 seconds, say: "I just want to make sure my line is working — are you still there?", 
still if they don't respond, end with "Alright, I'll let you go. Feel free to reach out to us at vikara.ai if you 
want to explore AI for your business. Have a great day!". And log this as a "no answer" in your system.
- Never ask for dates or times in a specific format
- Never read back raw formats like "2026-02-28" — always say "March 10th"
- If booking fails, say: "Hmm, something didn't go through — let me try that one more time" 
  and IMMEDIATELY call book_appointment again with the exact same details
  - Only give up after 2 failed attempts, then say: "I'm so sorry about this — our team will reach out to confirm manually. You'll still hear from us!" 
- Sound human — use "Got it", "Absolutely", "That makes sense", "Of course"
"""
                }
            ],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "book_appointment",
                        "description": "Books a free discovery session with the Vikara team and sends a Google Calendar invite to the customer.",
                        "parameters": {
                            "type": "object",
                            "required": ["name", "phone", "email", "date", "time", "purpose"],
                            "properties": {
                                "name":             {"type": "string",  "description": "Full name of the customer"},
                                "phone":            {"type": "string",  "description": "Customer phone number"},
                                "email":            {"type": "string",  "description": "Customer email for the calendar invite"},
                                "date":             {"type": "string",  "description": "Session date in YYYY-MM-DD format"},
                                "time":             {"type": "string",  "description": "Session time in HH:MM 24-hour format"},
                                "purpose":          {"type": "string",  "description": "Type of session based on customer need"},
                                "timezone":         {"type": "string",  "description": F"Customer timezone, default {DEFAULT_TIMEZONE}"},
                                "duration_minutes": {"type": "integer", "description": "Duration in minutes, default 30"},
                            },
                        },
                    },
                    "server": {
                        "url": f"{BACKEND_URL}/vapi/tool/book-appointment"
                    },
                }
            ],
            "temperature": 0.8,
        },

        "voice": {
            "provider":        "11labs",
            "voiceId":         "EXAVITQu4vr4xnSDxMaL",   # Sarah — warm, professional
            "stability":       0.4,
            "similarityBoost": 0.8,
            "useSpeakerBoost": True,
            "speed": 0.85
        },

        # ✅ Outbound opening — Maya introduces herself to the customer
        "firstMessage": "Hi there! This is Maya calling from Vikara — we're an AI consulting "
                        "firm that helps businesses build and scale with AI. I just wanted to reach out and see if your "
                        "team is exploring AI at all, and if a quick free session with one of our consultants might be valuable for you.",

        "serverUrl": f"{BACKEND_URL}/vapi/webhook",
    }


# Validate on import
if ENVIRONMENT:
    validate_config()


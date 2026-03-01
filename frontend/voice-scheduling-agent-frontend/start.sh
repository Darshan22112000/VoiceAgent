#!/bin/sh
envsubst < /app/dist/voice-scheduling-agent-frontend/browser/assets/env.template.js \
         > /app/dist/voice-scheduling-agent-frontend/browser/assets/env.js

echo "API_URL=$API_URL"
echo "VAPI_PUBLIC_KEY=$VAPI_PUBLIC_KEY"

serve -s /app/dist/voice-scheduling-agent-frontend/browser -l $PORT
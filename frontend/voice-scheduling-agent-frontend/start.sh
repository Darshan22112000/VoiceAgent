#!/bin/sh

# Replace placeholders in env.js with actual Railway environment variables
envsubst < /app/dist/voice-scheduling-agent-frontend/browser/assets/env.template.js \
         > /app/dist/voice-scheduling-agent-frontend/browser/assets/env.js

echo "Environment configured:"
echo "  API_URL=$API_URL"
echo "  VAPI_PUBLIC_KEY=$VAPI_PUBLIC_KEY"

# Start the server
npx serve -s /app/dist/voice-scheduling-agent-frontend/browser -l $PORT
FROM node:22.12.0-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build -- --configuration production

# ✅ Create assets folder and copy env.template.js
RUN mkdir -p dist/voice-scheduling-agent-frontend/browser/assets && \
    cp src/assets/env.template.js dist/voice-scheduling-agent-frontend/browser/assets/env.template.js

FROM node:22.12.0-alpine
RUN npm install -g serve
RUN apk add --no-cache gettext
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY start.sh ./
RUN chmod +x start.sh

EXPOSE 3000
CMD ["sh", "start.sh"]
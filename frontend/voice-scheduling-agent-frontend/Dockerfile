FROM node:22.12.0-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build -- --configuration production
RUN cp src/assets/env.template.js dist/voice-scheduling-agent-frontend/browser/assets/env.template.js

FROM node:22.12.0-alpine
RUN npm install -g serve
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/src/assets/env.template.js ./dist/voice-scheduling-agent-frontend/browser/assets/env.template.js
COPY start.sh ./
RUN chmod +x start.sh
RUN apk add --no-cache gettext

EXPOSE 3000
CMD ["sh", "start.sh"]
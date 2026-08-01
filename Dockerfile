# One image, both halves. The PWA is static, so it is built here and then
# served by FastAPI -- same origin, one deploy, no CORS.
#
# Build context is the repo root, since this needs app/ and server/.

FROM node:22-alpine AS app
WORKDIR /app
COPY app/package.json app/package-lock.json ./
RUN npm ci
COPY app/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /srv
COPY server/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY server/ ./server/
# main.py resolves the build relative to its own parent's parent.
COPY --from=app /app/build ./app/build
EXPOSE 8080
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8080"]

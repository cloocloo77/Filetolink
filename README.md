# Telegram File-to-Link Bot (2GB, Stream + Download)

Production-grade Telegram bot + FastAPI server that creates Telegram-backed links for files users upload.

## Project overview
- Users send a file to the bot.
- Bot stores Telegram identifiers (not file bytes) and returns generated links.
- FastAPI streams bytes from Telegram using range-aware HTTP responses.

## Features
- MTProto-backed file retrieval with **Pyrogram**.
- Supports Telegram files up to **2GB** (enforced by `MAX_FILE_SIZE`).
- Direct download links (`/d/{token}`).
- Stream links for video/audio (`/s/{token}`) with HTTP range support.
- Async end-to-end architecture.
- Duplicate caching using `file_unique_id`.
- Auto-expiry + periodic cleanup.
- Concurrent users supported.
- `/start` and `/help` commands.
- Optional forced download header.

## Architecture
1. **Bot ingest layer** (`app/bot/handlers.py`) captures user files and registers metadata.
2. **Registry layer** (`app/services/file_registry.py`) deduplicates and persists tokens.
3. **API layer** (`app/api/stream.py`) serves range-enabled streaming and downloads.
4. **Storage layer** (`app/storage/db.py`) tracks token/file metadata and expiry.

No permanent file storage required, ideal for Heroku ephemeral disk constraints.

## BotFather setup
1. Open BotFather in Telegram.
2. Run `/newbot` and get `BOT_TOKEN`.
3. Set `/setprivacy` -> disable if your use-case requires group file intake.

## Configuration
Copy `.env.example` to `.env`:
- `BOT_TOKEN`
- `API_ID`
- `API_HASH`
- `BASE_URL`
- `PORT`
- `DATABASE_URL`
- `FILE_EXPIRY_HOURS`
- `MAX_FILE_SIZE`
- `OWNER_ID` (optional)
- `FORCE_DOWNLOAD` (optional)
- `RUN_BOT` (set `false` on web-only dynos when running separate worker)

## Local run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --host 0.0.0.0 --port 8000
```

## VPS deployment (Ubuntu)
1. Install dependencies:
```bash
sudo apt update && sudo apt install -y python3.11-venv nginx git
```
2. Clone repository to `/opt/filetolink`.
3. Create virtualenv and install requirements.
4. Configure `.env` with your real values.
5. Install systemd unit:
```bash
sudo cp deploy/filetolink.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now filetolink
```
6. Configure Nginx with `deploy/nginx.conf`, then:
```bash
sudo nginx -t && sudo systemctl reload nginx
```
7. Add TLS via certbot.

## Heroku deployment
Because Heroku filesystem is ephemeral, this app stores metadata in DB and streams from Telegram.
1. Create app and add buildpacks (Python).
2. Set config vars from `.env.example`.
3. Use managed DB (e.g., Postgres) and set `DATABASE_URL` accordingly.
4. Deploy:
```bash
git push heroku main
heroku ps:scale web=1 worker=1
```
5. Set `RUN_BOT=false` for web dyno and `RUN_BOT=true` for worker dyno to avoid duplicate polling.

## Google Colab deployment
1. Upload project or clone repo in Colab.
2. Install deps and run FastAPI with tunnel:
```python
!pip install -r requirements.txt
!python -m uvicorn main:app --host 0.0.0.0 --port 8000
```
3. Use `cloudflared` or `ngrok` to expose URL and update `BASE_URL`.

## Docker usage
```bash
docker compose up --build -d
```
Service runs on port `8000`.

## Nginx reverse proxy setup
Use `deploy/nginx.conf` as base. Important settings:
- `client_max_body_size 0`
- `proxy_buffering off`
- `proxy_request_buffering off`

## API endpoints
- `GET /health`: health check.
- `GET /d/{token}`: download endpoint (range capable).
- `GET /s/{token}`: streaming endpoint for audio/video.

## Bot reply example
After upload:
- Name: `movie.mkv`
- Size: `104857600 bytes`
- MIME: `video/x-matroska`
- Download: `https://domain/d/<token>`
- Stream: `https://domain/s/<token>`

## Scaling notes
- Use Postgres for multi-instance deployment.
- Front with Nginx/CDN for connection handling.
- Increase worker count depending on outbound bandwidth.

## Performance tuning notes
- Current chunking uses 1MB stream chunks.
- Keep asyncio event loop free of blocking I/O.
- Tune DB pool for high concurrency.

## Security considerations
- Use HTTPS only.
- Rotate bot/API secrets.
- Set low expiry for sensitive files.
- Consider signed JWT links if stronger access control is needed.

## Troubleshooting
- `404 link not found`: expired token or cleaned record.
- `416 invalid range`: client requested invalid byte range.
- Slow streams: likely Telegram/DC latency or VPS bandwidth.
- Heroku sleeping dynos: use paid dynos for steady performance.

## Example command usage
- `/start`
- `/help`
- Send a file directly in private chat.

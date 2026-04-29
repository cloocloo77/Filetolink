# FileToLink — Telegram File Sharing via FastAPI

A production-ready Telegram bot + FastAPI service that turns Telegram uploads into temporary download and streaming links.

---

## 1) What this project does

When a user uploads a file to your bot:

1. The bot receives metadata (`file_id`, `file_unique_id`, name, size, mime).
2. The app stores only metadata in your database.
3. The API serves file bytes directly from Telegram using MTProto when users open generated links.

This means:
- ✅ No long-term local file storage required.
- ✅ Works well on stateless/ephemeral hosts.
- ✅ Supports range requests for media players.

---

## 2) Core features

- Telegram ingestion using **Pyrogram**.
- Download links: `GET /d/{token}`.
- Streaming links: `GET /s/{token}`.
- HTTP range support (`206 Partial Content`).
- Configurable max upload size (`MAX_FILE_SIZE`, default 2GB).
- Token-based linking.
- Auto-expiry with periodic DB cleanup.
- Deduplication by `file_unique_id`.
- Docker + systemd + Nginx deployment examples.

---

## 3) Tech stack

- **Python 3.11**
- **FastAPI** + **Uvicorn**
- **Pyrogram** (+ tgcrypto)
- **SQLAlchemy 2 async**
- **SQLite/aiosqlite** by default (Postgres recommended in production)

---

## 4) Repository structure

```text
.
├── app/
│   ├── api/                 # HTTP endpoints (/health, /d/{token}, /s/{token})
│   ├── bot/                 # Telegram bot handlers
│   ├── services/            # Telegram client, file registry, token generation
│   └── storage/             # SQLAlchemy models and DB helpers
├── deploy/
│   ├── filetolink.service   # systemd unit template
│   └── nginx.conf           # reverse proxy template
├── main.py                  # FastAPI app lifecycle and startup
├── config.py                # env-driven settings model
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## 5) Environment variables

Copy `.env.example` to `.env` and set values:

| Variable | Required | Description |
|---|---:|---|
| `BOT_TOKEN` | Yes | Telegram bot token from BotFather |
| `API_ID` | Yes | Telegram API ID |
| `API_HASH` | Yes | Telegram API hash |
| `BASE_URL` | Yes | Public HTTPS base URL, e.g. `https://files.example.com` |
| `PORT` | No | App port (default: `8000`) |
| `DATABASE_URL` | No | SQLAlchemy async URL (default SQLite local file) |
| `FILE_EXPIRY_HOURS` | No | Link validity window (default: `24`) |
| `MAX_FILE_SIZE` | No | Max accepted upload bytes (default: `2147483648`) |
| `OWNER_ID` | No | Optional owner user ID |
| `FORCE_DOWNLOAD` | No | If `true`, sets attachment header |

---

## 6) Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl -i http://127.0.0.1:8000/health
```

---

## 7) Production deployment guide (recommended)

### Option A: VPS + systemd + Nginx

1. Install prerequisites:
```bash
sudo apt update
sudo apt install -y python3.11-venv nginx git
```
2. Clone into `/opt/filetolink`.
3. Create virtualenv + install dependencies.
4. Create `/opt/filetolink/.env`.
5. Install service:
```bash
sudo cp deploy/filetolink.service /etc/systemd/system/filetolink.service
sudo systemctl daemon-reload
sudo systemctl enable --now filetolink
```
6. Configure Nginx from `deploy/nginx.conf` and reload:
```bash
sudo nginx -t
sudo systemctl reload nginx
```
7. Add TLS (Let's Encrypt/certbot).

### Option B: Docker

```bash
docker compose up --build -d
```

---

## 8) API reference

### `GET /health`
Returns service health.

### `GET /d/{token}`
Download endpoint. Supports `Range`.

### `GET /s/{token}`
Streaming endpoint for audio/video MIME types only.

**Common errors**
- `404`: token missing or expired.
- `400`: `/s/` used for non-streamable MIME.
- `416`: invalid range request.

---

## 9) Operational recommendations

- Prefer **PostgreSQL** over SQLite in multi-instance deployments.
- Use HTTPS only; never expose plain HTTP publicly.
- Set realistic `FILE_EXPIRY_HOURS` for your threat model.
- Keep `BASE_URL` aligned with your external domain.
- Monitor memory and outbound bandwidth (Telegram streaming heavy workloads).

---

## 10) Known limitations

- Availability and speed depend on Telegram fetch latency.
- Very high concurrency benefits from horizontal scaling and tuned DB.
- Bot and API run in same process by default; split if needed for very large workloads.

---

## 11) Pre-deploy checklist

- [ ] `.env` exists with real credentials.
- [ ] `BASE_URL` points to your public HTTPS domain.
- [ ] DB URL is persistent for production.
- [ ] Reverse proxy configured for large/streaming responses.
- [ ] Service manager enabled (`systemd`/container restart policy).
- [ ] Health endpoint reachable.

---

## 12) License

MIT License. See `LICENSE`.

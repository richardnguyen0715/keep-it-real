This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

---

## Local Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see the app.

---

## Public Demo (expose to internet)

This setup uses **Docker + Nginx + Cloudflare Tunnel** to serve the app securely over the internet from your local machine — no cloud server required.

### Architecture

```
Internet → Cloudflare Tunnel (HTTPS + DDoS protection)
                ↓
           Nginx :80 (rate limiting, security headers)
                ↓
         Next.js app :3000 (Docker container)
```

### Prerequisites

```bash
# Docker Desktop must be running
# Install cloudflared (one-time)
brew install cloudflare/cloudflare/cloudflared
```

### Start

```bash
# 1. Start the app + nginx containers
cd projects/new-era
docker compose up -d --build

# 2. Open a public HTTPS tunnel (get a random URL on trycloudflare.com)
nohup cloudflared tunnel --url http://localhost:80 > /tmp/cloudflared.log 2>&1 &

# 3. Get the public URL
grep -o 'https://.*trycloudflare\.com' /tmp/cloudflared.log
```

Share the printed URL — it is immediately accessible over HTTPS.

### Stop

```bash
# Stop the tunnel
kill $(pgrep cloudflared)

# Stop containers
docker compose down
```

### Check status

```bash
# Tunnel logs
tail -f /tmp/cloudflared.log

# Container status
docker compose ps
```

---

## Security

| Layer | What it does |
|-------|-------------|
| **Cloudflare Tunnel** | HTTPS/TLS termination, DDoS protection, no open firewall ports |
| **Rate limiting** | 30 req/min per IP for pages; 120 req/min for static assets |
| **Connection limit** | Max 20 simultaneous connections per IP |
| **Security headers** | HSTS, CSP, X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy |
| **Bad bot blocking** | Blocks common scanners (nikto, sqlmap, nmap, etc.) |
| **Hidden attack surface** | Nginx version hidden; blocks `.env`, `.git`, hidden files |
| **Request timeouts** | Prevents slow-loris and hung connection attacks |
| **Body size limit** | Max 2 MB request body |

> **Note:** The free `trycloudflare.com` tunnel has no uptime guarantee and the URL changes on every restart. For a permanent URL, create a [named Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps) with a Cloudflare account and a custom domain.

---

## Project Structure

```
.
├── src/                  # Next.js app source
├── nginx/
│   └── nginx.conf        # Hardened reverse proxy config
├── Dockerfile            # Multi-stage production build
├── docker-compose.yml    # App + Nginx services
└── public/               # Static assets
```

This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

---

## Deploy from Scratch

Complete guide to get this website running and publicly accessible on the internet from a fresh machine.

### Step 1 — Install system dependencies

> Skip any tool you already have.

**macOS (Homebrew)**

```bash
# Install Homebrew if not present
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Git
brew install git

# Docker Desktop (includes docker compose)
brew install --cask docker
open -a Docker   # launch Docker Desktop and wait for it to fully start

# Cloudflare Tunnel CLI
brew install cloudflare/cloudflare/cloudflared
```

**Linux (Debian/Ubuntu)**

```bash
# Git + Docker
sudo apt update && sudo apt install -y git docker.io docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker $USER   # log out and back in after this

# Cloudflare Tunnel CLI
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb && rm cloudflared.deb
```

### Step 2 — Clone the repository

```bash
git clone https://github.com/richardnguyen0715/keep-it-real.git
cd keep-it-real/projects/new-era
```

### Step 3 — Build and start the containers

```bash
docker compose up -d --build
```

This builds the Next.js production image and starts two containers:
- `new-era-app` — the Next.js app on port 3000 (internal only)
- `new-era-nginx` — hardened Nginx reverse proxy on port 80

Verify both are healthy:

```bash
docker compose ps
# Expected: both containers show "Up"

curl -s -o /dev/null -w "%{http_code}" http://localhost:80
# Expected: 200
```

### Step 4 — Open a public HTTPS tunnel

```bash
nohup cloudflared tunnel --url http://localhost:80 > /tmp/cloudflared.log 2>&1 &
```

Wait ~10 seconds, then get your public URL:

```bash
grep -o 'https://.*trycloudflare\.com' /tmp/cloudflared.log
```

You will see something like:

```
https://random-words-here.trycloudflare.com
```

Open that URL in any browser — your site is live on the internet over HTTPS. Share it with anyone.

---

## Manage the running demo

```bash
# View live tunnel logs
tail -f /tmp/cloudflared.log

# View container logs
docker compose logs -f

# Container status
docker compose ps

# Stop the public tunnel (site goes offline, containers keep running)
kill $(pgrep cloudflared)

# Stop everything
kill $(pgrep cloudflared); docker compose down
```

---

## Restart after a reboot

The tunnel URL changes every time. After rebooting your machine, repeat Steps 3 and 4:

```bash
cd keep-it-real/projects/new-era
docker compose up -d
nohup cloudflared tunnel --url http://localhost:80 > /tmp/cloudflared.log 2>&1 &
sleep 10 && grep -o 'https://.*trycloudflare\.com' /tmp/cloudflared.log
```

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

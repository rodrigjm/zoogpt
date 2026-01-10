# Cloudflare Tunnel Setup for Zoocari

This guide configures HTTPS access for Zoocari using Cloudflare Tunnel, enabling mobile voice recording (which requires a secure context).

## Why HTTPS is Required

Browsers block microphone access (`getUserMedia()`) on insecure origins:

| Environment | Voice Input | Notes |
|-------------|-------------|-------|
| `localhost:8501` | Works | Localhost is trusted |
| `http://10.0.0.x:8501` | Blocked | Insecure context |
| `https://zoocari.example.com` | Works | Secure context |

## Prerequisites

- Cloudflare account (free tier works)
- Domain with DNS managed by Cloudflare
- Docker and docker-compose installed

## Setup Options

### Option A: Token-Based (Recommended for Docker)

This method uses a tunnel token from the Cloudflare dashboard - no local credentials needed.

#### Step 1: Create Tunnel in Cloudflare Dashboard

1. Go to [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/)
2. Navigate to **Networks** > **Tunnels**
3. Click **Create a tunnel**
4. Select **Cloudflared** connector
5. Name your tunnel: `zoocari`
6. Click **Save tunnel**

#### Step 2: Configure Tunnel Route

In the tunnel configuration:

1. **Public Hostname**:
   - Subdomain: `zoocari` (or your preferred subdomain)
   - Domain: Select your domain
   - Path: (leave empty)

2. **Service**:
   - Type: `HTTP`
   - URL: `zoocari:8501`

3. Click **Save hostname**

#### Step 3: Get Tunnel Token

1. In the tunnel overview, click **Configure**
2. Go to the **Install connector** section
3. Copy the token from the Docker command (the long string after `--token`)

#### Step 4: Configure Environment

Add to your `.env` file:

```bash
CLOUDFLARE_TUNNEL_TOKEN=eyJhIjoi...your-long-token-here...
```

#### Step 5: Start with Tunnel

```bash
# Start Zoocari with Cloudflare tunnel
docker compose --profile tunnel up -d

# View tunnel logs
docker logs zoocari-tunnel -f
```

---

### Option B: Credentials File (CLI Setup)

This method uses local cloudflared CLI to create tunnel credentials.

#### Step 1: Install cloudflared

```bash
# macOS
brew install cloudflare/cloudflare/cloudflared

# Linux (Debian/Ubuntu)
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb

# Verify installation
cloudflared --version
```

#### Step 2: Authenticate with Cloudflare

```bash
cloudflared tunnel login
```

This opens a browser to authenticate. Select the domain you want to use.

#### Step 3: Create Tunnel

```bash
cloudflared tunnel create zoocari
```

This outputs:
- Tunnel ID (e.g., `a1b2c3d4-e5f6-7890-abcd-ef1234567890`)
- Credentials file path (e.g., `~/.cloudflared/a1b2c3d4-....json`)

#### Step 4: Copy Credentials

```bash
# Copy credentials to project
cp ~/.cloudflared/YOUR_TUNNEL_ID.json ./cloudflare/credentials.json
```

#### Step 5: Update Configuration

Edit `cloudflare/config.yml`:

```yaml
tunnel: YOUR_TUNNEL_ID
credentials-file: /etc/cloudflared/credentials.json

ingress:
  - hostname: zoocari.yourdomain.com
    service: http://zoocari:8501
  - service: http_status:404
```

#### Step 6: Create DNS Route

```bash
cloudflared tunnel route dns zoocari zoocari.yourdomain.com
```

#### Step 7: Start with Tunnel

```bash
docker compose --profile tunnel up -d
```

---

## Verification

### Check Tunnel Status

```bash
# View tunnel container logs
docker logs zoocari-tunnel

# Check Cloudflare dashboard
# Networks > Tunnels > zoocari should show "Healthy"
```

### Test HTTPS Access

1. Open `https://zoocari.yourdomain.com` in browser
2. Click the voice recording button
3. Grant microphone permission when prompted
4. Test voice input

### Expected Log Output

```
INFO[0000] Starting tunnel
INFO[0000] Registered tunnel connection
INFO[0000] Connection established
```

---

## Troubleshooting

### Tunnel Won't Connect

```bash
# Check container status
docker ps -a | grep cloudflared

# View detailed logs
docker logs zoocari-tunnel --tail 100

# Verify token is set
docker compose --profile tunnel config | grep TUNNEL_TOKEN
```

### "Service Unavailable" Error

The Zoocari app may not be ready yet:

```bash
# Check if Zoocari is running
docker logs zoocari-app --tail 50

# Ensure zoocari container starts first
docker compose --profile tunnel up zoocari -d
sleep 10
docker compose --profile tunnel up cloudflared -d
```

### DNS Not Resolving

```bash
# Check DNS propagation
dig zoocari.yourdomain.com

# Verify route exists in Cloudflare dashboard
# Networks > Tunnels > zoocari > Public Hostname
```

### WebSocket Connection Issues

Streamlit uses WebSockets. If the UI loads but doesn't respond:

1. Check tunnel supports WebSocket upgrades
2. In Cloudflare dashboard, ensure **WebSockets** is enabled for your domain
3. Check for any WAF rules blocking WebSocket connections

---

## Security Notes

- **Never commit credentials.json** - it's in `.gitignore`
- **Rotate tokens** periodically via Cloudflare dashboard
- **Use Access policies** for additional authentication (optional)
- Tunnel traffic is encrypted end-to-end

---

## Quick Reference

```bash
# Start with tunnel
docker compose --profile tunnel up -d

# Start without tunnel (local only)
docker compose up -d

# Stop everything
docker compose --profile tunnel down

# View tunnel logs
docker logs zoocari-tunnel -f

# Restart tunnel only
docker compose --profile tunnel restart cloudflared
```

---

## Architecture

```
Internet                    Cloudflare Edge              Your Server
   |                              |                           |
   |  HTTPS request               |                           |
   |----------------------------->|                           |
   |                              |  Tunnel (encrypted)       |
   |                              |-------------------------->|
   |                              |                           |
   |                              |        Docker Network     |
   |                              |    +------------------+   |
   |                              |    | cloudflared      |   |
   |                              |--->| (tunnel client)  |   |
   |                              |    +--------|---------+   |
   |                              |             |              |
   |                              |             v              |
   |                              |    +------------------+   |
   |                              |    | zoocari:8501    |   |
   |                              |    | (Streamlit app) |   |
   |                              |    +------------------+   |
```

The tunnel establishes an outbound connection from your server to Cloudflare's edge, so no inbound ports need to be opened on your firewall.

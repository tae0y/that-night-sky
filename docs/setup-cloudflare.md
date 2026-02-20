# Set Up Cloudflare Tunnel

This page describes how to create a Cloudflare Tunnel to expose ThatNightSky to the internet without port forwarding.

## Prerequisites

- A [Cloudflare account](https://dash.cloudflare.com) with a domain added and active
- Docker Compose running the app (see [setup-docker.md](setup-docker.md))
- `CLOUDFLARE_TUNNEL_TOKEN` available to add to the `.env` file on the server

## Create the tunnel

1. Go to [Cloudflare Zero Trust](https://one.dash.cloudflare.com) → **Networks** → **Tunnels** → **Create a tunnel**.

1. Select **Cloudflared** as the connector type, enter a tunnel name (e.g. `thatnightsky`), then click **Save tunnel**.

1. Copy the tunnel token shown on the next screen.
   This value goes into `CLOUDFLARE_TUNNEL_TOKEN` in your server's `.env` file.

1. Under **Public Hostnames**, add a hostname:

    | Field | Value |
    |-------|-------|
    | Subdomain | `sky` (or any name you prefer) |
    | Domain | your connected domain |
    | Service type | `HTTP` |
    | URL | `sky:8501` |

    > **Important:** The service URL must use the Compose service name `sky`, not `localhost`. Both containers share the `internal` bridge network defined in `docker-compose.yml`.

1. Click **Save hostname**.
   The tunnel status will remain **Inactive** until the `cloudflared` container starts.

## Add the token to the server

On the home server, open the `.env` file at the project root and add:

```env
CLOUDFLARE_TUNNEL_TOKEN=<token copied in step 3>
```

The full set of required variables:

| Variable | Description |
|----------|-------------|
| `VWORLD_API_KEY` | Korean Spatial Information Open Platform API key |
| `ANTHROPIC_API_KEY` | Claude API key |
| `CLOUDFLARE_TUNNEL_TOKEN` | Tunnel token from Cloudflare Zero Trust |

## Start the containers

```powershell
# PowerShell (home server)
docker compose -f docker/docker-compose.yml up -d
```

The `cloudflared` service depends on the `sky` health check passing, so it starts roughly 15–45 seconds after Docker Compose begins. Once both containers are running, the tunnel status in the Cloudflare dashboard changes to **Healthy**.

## Verify

1. Open the Cloudflare Zero Trust dashboard → **Networks** → **Tunnels** — confirm the tunnel shows **Healthy**.
1. Open `https://<subdomain>.<domain>` in a browser — the app should load.
1. Submit a location and confirm the star chart renders and the WebSocket session stays connected.

## Remove

1. Stop and remove the containers:

    ```powershell
    # PowerShell (home server)
    docker compose -f docker/docker-compose.yml down
    ```

1. In the Cloudflare Zero Trust dashboard → **Networks** → **Tunnels**, select the tunnel → **Delete**.

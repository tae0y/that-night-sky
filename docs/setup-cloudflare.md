# Set Up Cloudflare Tunnel

This page describes how to create a Cloudflare Tunnel to expose ThatNightSky to the internet without port forwarding.

## Prerequisites

- A [Cloudflare account](https://dash.cloudflare.com)
- A registered domain (any registrar)
- Docker Compose running the app (see [setup-docker.md](setup-docker.md))
- `CLOUDFLARE_TUNNEL_TOKEN` available to add to the `.env` file on the server

## Add the domain to Cloudflare

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com) → **Add a site** → enter your domain name → select a plan.

1. Cloudflare scans existing DNS records and shows two nameservers (e.g. `emma.ns.cloudflare.com`, `ivan.ns.cloudflare.com`). Copy both.

1. Log in to your domain registrar (e.g. Gabia, Hosting.kr, Namecheap) and open the nameserver settings for the domain.

1. Replace the current nameservers with the two Cloudflare nameservers copied in the previous step.

   > **Important:** Nameserver propagation can take up to 48 hours, though it usually completes within a few minutes.

1. Back in the Cloudflare dashboard, click **Check nameservers**. Once propagation completes, the domain status changes to **Active**.

1. In the Cloudflare dashboard, go to **DNS** → **Records** → **Add record**. Add the records needed for your subdomain (Cloudflare Tunnel creates a CNAME automatically when you add a public hostname in the tunnel config, so manual DNS records are only needed for non-tunnel services).

## Create the tunnel

1. Go to [Cloudflare Dashboard](https://one.dash.cloudflare.com) → **Networks** → **Connectors** → **Create a tunnel**.

1. Select **Cloudflared** as the connector type, enter a tunnel name (e.g. `thatnightsky`), then click **Save tunnel**.

1. Copy the tunnel token from the install command shown on screen (the long string at the end of `cloudflared service install <token>`). Save it for the `.env` file.

1. Under **Public Hostnames**, add a route with your subdomain, domain, and service URL.

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

```bash
# bash/zsh
docker compose -f docker/docker-compose.yml --env-file .env up -d
```

```powershell
# PowerShell
docker compose -f docker/docker-compose.yml --env-file .env up -d
```

The `cloudflared` service depends on the `sky` health check passing, so it starts roughly 15–45 seconds after Docker Compose begins. Once both containers are running, the tunnel status in the Cloudflare dashboard changes to **Healthy**.

## Verify

1. Open the Cloudflare Zero Trust dashboard → **Networks** → **Tunnels** — confirm the tunnel shows **Healthy**.
1. Open `https://<subdomain>.<domain>` in a browser — the app should load.
1. Submit a location and confirm the star chart renders and the WebSocket session stays connected.

## Remove

1. Stop and remove the containers:

    ```bash
    # bash/zsh
    docker compose -f docker/docker-compose.yml --env-file .env down
    ```

    ```powershell
    # PowerShell
    docker compose -f docker/docker-compose.yml --env-file .env down
    ```

1. In the Cloudflare Zero Trust dashboard → **Networks** → **Tunnels**, select the tunnel → **Delete**.

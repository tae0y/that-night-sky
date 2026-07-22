# Set Up GitHub Actions Deployment

This page describes how to auto-deploy ThatNightSky to the home server on every push to `main`, using a self-hosted GitHub Actions runner.

## Prerequisites

- Docker Compose running the app on the home server (see [setup-docker.md](setup-docker.md))

## Register the runner

1. Settings → Actions → Runners → New self-hosted runner → pick the home server's OS/architecture.
2. Follow the instructions described on the page. It shows registration token (expires in ~1 hour) and setup commands.
3. Registration succeeds when the runner shows Idle (green) under Settings → Actions → Runners.

## Configure Actions permissions

1. Go to Settings → Actions → General → Actions permissions
2. Select Allow &lt;username&gt;, and select non-&lt;username&gt;, actions and reusable workflows.

## Verify

1. Push to `main` → confirm **Deploy to local server** succeeds on the self-hosted runner.
2. On the home server: `docker compose -f docker/docker-compose.yml ps` — confirm containers restarted.
3. Open `/healthz` through the deployed URL — confirm it responds.

## Remove

1. Stop and uninstall the runner service (It depends on your machine)
2. Settings → Actions → Runners → select the runner → Remove.
3. Delete `.github/workflows/deploy.yml` if no longer needed.


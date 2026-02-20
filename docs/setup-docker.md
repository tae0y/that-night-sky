# Run ThatNightSky in Docker

This page describes how to build and run the ThatNightSky Streamlit app using Docker Compose.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + Compose plugin)
- A `.env` file at the project root with the required environment variables

## Environment variables

If no `.env` file exists, create one:

```bash
cp .env.example .env
```

Required keys:

| Variable | Description |
|----------|-------------|
| `VWORLD_API_KEY` | Korean Spatial Information Open Platform API key ([vworld.kr](https://www.vworld.kr)) |
| `ANTHROPIC_API_KEY` | Claude API key ([console.anthropic.com](https://console.anthropic.com)) |

## Run locally

Use `docker-compose.override.yml` together with the base file. The override exposes port 8501 directly to the host and replaces the external network with a local one, so no external dependency is needed.

1. From the repository root, start the app:

    ```bash
    docker compose -f docker/docker-compose.yml -f docker/docker-compose.override.yml up --build
    ```

1. Open `http://localhost:8501` in a browser.

    To stop:

    ```bash
    docker compose -f docker/docker-compose.yml -f docker/docker-compose.override.yml down
    ```

## Production deployment

For internet-facing deployments, use Cloudflare Tunnel instead of exposing ports directly.
See [setup-cloudflare.md](setup-cloudflare.md) for the full setup.

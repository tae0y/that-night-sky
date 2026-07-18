# ThatNightSky Frontend

This page describes how to run the React frontend for ThatNightSky.

## Prerequisites

- [Node.js](https://nodejs.org) 20+
- The FastAPI backend running on port 8000 (see the [project README](../README.md))

## Run

1. Install dependencies.

    ```bash
    npm install
    ```

1. Start the dev server.

    ```bash
    npm run dev
    ```

   The dev server proxies `/api` requests to the backend at `http://localhost:8000`.

## Build

```bash
npm run build
```

The production bundle is written to `dist/` and served by the FastAPI backend in the Docker deployment.

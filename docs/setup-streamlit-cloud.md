# Deploy ThatNightSky to Streamlit Community Cloud

This page describes how to deploy the ThatNightSky Streamlit app to Streamlit Community Cloud (free tier).

## Prerequisites

- GitHub account with push access to this repository
- [Streamlit Community Cloud](https://share.streamlit.io) account (sign up with GitHub)
- `VWORLD_API_KEY` and `ANTHROPIC_API_KEY` values

## Dependency file

Streamlit Community Cloud recognises `uv.lock` natively (since November 2024). No `requirements.txt` is needed — committing `uv.lock` is sufficient.

```bash
git ls-files uv.lock   # should print "uv.lock"
```

## Deploy

1. Push your changes to the `main` branch.

    ```bash
    git push origin main
    ```

1. Go to [share.streamlit.io](https://share.streamlit.io) and log in with GitHub.

1. Click **Create app** → **Deploy a public app from GitHub**.

1. Fill in the app settings:

    | Field | Value |
    |-------|-------|
    | Repository | `<your-github-username>/ThatNightSky` |
    | Branch | `main` |
    | Main file path | `src/thatnightsky/app.py` |

1. Open **Advanced settings** and paste the following into the **Secrets** field:

    ```toml
    VWORLD_API_KEY = "your_key_here"
    ANTHROPIC_API_KEY = "your_key_here"
    ```

    > **Important:** Secrets are exposed automatically as environment variables. The app reads them via `os.environ`, so no code changes are needed.

1. Click **Deploy**.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Build fails — `poetry not found` | Cloud misreads `pyproject.toml` as Poetry format | Verify `uv.lock` is committed |
| `KeyError: VWORLD_API_KEY` | Secrets not entered | Add keys in Advanced settings → Secrets |
| `ModuleNotFoundError: thatnightsky` | `src/` layout not recognised | Check package config in `pyproject.toml` |
| App restarts with memory error | Loading `hip_main.dat` (51 MB) | Verify `@st.cache_resource` is applied in `compute.py` |
| Cold start takes 30–60 seconds | Astronomical data reloaded after sleep | Expected behaviour; loading spinner handles UX |

## Security notes

- `.env` and `.streamlit/secrets.toml` are listed in `.gitignore` and will never be committed.
- API keys are managed exclusively through Streamlit Cloud dashboard Secrets.
- The app limits narrative generation to 3 times per session to control Anthropic API costs.

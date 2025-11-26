![](images/logo.png)

---

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Vue 3](https://img.shields.io/badge/vue-3.x-green.svg)](https://vuejs.org/)

# RedInk - AI Graphic Generator for Xiaohongshu

> Make spreading no longer a threshold, make creation never so simple

[English Version](./README_en.md) | [中文版](./README.zh.md)

![](images/index.gif)

<p align="center">
  <em>RedInk Home</em>
</p>

## About

Generate complete Xiaohongshu posts from a single sentence or image.

---

## 🔄 Upstream Sync

This project is a customized version of [HisMax/RedInk](https://github.com/HisMax/RedInk), optimized for Vercel deployment.

### Project Relationship
- **Upstream**: https://github.com/HisMax/RedInk
- **Fork**: This repository includes Vercel adaptation, environment variable support, etc.

### Manual Sync
To sync with the latest upstream changes:

```bash
./scripts/sync_upstream.sh
```

### Custom Modifications
See [CUSTOM_MODIFICATIONS.md](./CUSTOM_MODIFICATIONS.md) for details.

---

## ⚙️ Configuration & Deployment

This guide covers environment variables, local development setup, and Vercel deployment options.

### 1. Environment Variables

Configure these variables in your `.env` file (local) or Vercel Project Settings (production).

| Variable | Required | Default | Description | Where to Retrieve |
| :--- | :--- | :--- | :--- | :--- |
| `GOOGLE_CLOUD_API_KEY` | **Yes** | - | API Key for Google Gemini (Text & Image) | [Google AI Studio](https://aistudio.google.com/) |
| `IMAGE_API_KEY` | No | - | API Key for Custom Image Provider | Your provider dashboard |
| `TEXT_API_KEY` | No | - | API Key for Custom Text Provider | Your provider dashboard |
| `TEXT_API_BASE_URL` | No | `https://api.bltcy.ai` | Base URL for Custom Text Provider | Your provider docs |
| `FLASK_DEBUG` | No | `True` | Debug mode toggle | - |
| `FLASK_HOST` | No | `0.0.0.0` | Server host | - |
| `FLASK_PORT` | No | `12398` | Server port | - |
| `CORS_ORIGINS` | No | `http://localhost:5173...` | Allowed CORS origins | - |
| `OUTPUT_DIR` | No | `output` | Local image output directory | - |
| `STORAGE_BACKEND` | No | `local` | Storage backend (`local`, `vercel_blob`, `vercel_kv`) | - |
| `VERCEL_BLOB_READ_WRITE_TOKEN`| No | - | Vercel Blob Token | Vercel Dashboard (Storage) |
| `VERCEL_KV_REST_API_URL` | No | - | Vercel KV URL | Vercel Dashboard (Storage) |
| `VERCEL_KV_REST_API_TOKEN` | No | - | Vercel KV Token | Vercel Dashboard (Storage) |
| `IMAGE_PROVIDER` | No | `google_genai` | Active image provider name | - |

### 2. Image Provider Configuration Strategies

RedInk offers two ways to configure image providers:

| Feature | Option A: Config File (`image_providers.yaml`) | Option B: Env-Only |
| :--- | :--- | :--- |
| **Setup Complexity** | Higher (requires managing YAML file) | Lower (just env vars) |
| **Provider Support** | **All** (Custom, OpenAI, Google, etc.) | **Google Gemini Only** |
| **Flexibility** | High (detailed params per provider) | Low (defaults only) |
| **Deployment** | Must commit file or allow in `.gitignore` | Easy (just set envs) |
| **Best For** | Power users, Custom APIs, multiple providers | Quick start, Google users |

### 3. Local Development Setup

**Prerequisites:**
- Python 3.11+
- Node.js 18+ & pnpm
- [uv](https://github.com/astral-sh/uv) (Python package manager)

#### Option A: With `image_providers.yaml` (Recommended for Custom Providers)

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd RedInk
   ```

2. **Configure Environment:**
   ```bash
   cp .env.example .env
   cp image_providers.yaml.example image_providers.yaml
   ```
   - Edit `.env` with your API keys.
   - Edit `image_providers.yaml` to configure your specific provider.

3. **Install Dependencies & Run:**
   ```bash
   # Backend
   uv sync
   uv run python -m backend.app

   # Frontend (in a new terminal)
   cd frontend
   pnpm install
   pnpm dev
   ```

#### Option B: Env-Only (Quick Start / Google GenAI)

1. **Clone the repository.**

2. **Configure Environment:**
   ```bash
   cp .env.example .env
   ```
   - Edit `.env` and set `GOOGLE_CLOUD_API_KEY`.
   - **Skip** creating `image_providers.yaml`.

3. **Install Dependencies & Run** as above.

### 4. Vercel Deployment

For detailed instructions, see [Vercel Deployment Guide](docs/vercel.md).

#### Method 1: Using Vercel Dashboard (Recommended)
1. Fork this repository.
2. Import project in Vercel Dashboard.
3. In **Environment Variables**, add the required keys (e.g., `GOOGLE_CLOUD_API_KEY`).
4. (Optional) Bind **Vercel KV** storage for persistence.
5. Deploy.

#### Method 2: Using `vercel.json` & CLI
1. Configure `vercel.json` (already present) for build settings.
2. Use Vercel CLI to deploy:
   ```bash
   npm i -g vercel
   vercel link
   vercel env pull .env.local  # Pull envs if needed
   vercel deploy
   ```
   *Note: Do not commit secrets to `vercel.json`.*

### 5. Troubleshooting

**Common Pitfalls:**

- **`image_providers.yaml` not found:** The system will fallback to the default Google Gemini configuration. If you are trying to use a custom provider, ensure the file exists and is readable.
- **API Key Errors:** Double-check that `GOOGLE_CLOUD_API_KEY` or `IMAGE_API_KEY` are set correctly in `.env` (local) or Vercel Environment Variables.
- **Vercel Storage:** If `STORAGE_BACKEND` is set to `vercel_kv` but no database is bound, the app will fail to save history. Check `KV_URL` presence.
- **Provider Mismatch:** If you set `IMAGE_PROVIDER=image_api` but didn't provide `image_providers.yaml`, the app will fail because `image_api` configuration is missing from the default fallback.

---

## ⚠️ Notes

1. **API Quotas**:
   - Be aware of Gemini and Image API quotas.
   - It is recommended to disable High Concurrency mode for free trial accounts.

2. **Generation Time**:
   - Image generation takes time, please be patient.

---

## 🤝 Contributing

Issues and Pull Requests are welcome!

## 📄 License

CC BY-NC-SA 4.0

# Custom Modifications List (自定义修改清单)

This document records the specific modifications made to this fork to support Vercel deployment and other customizations. These files should be preserved during upstream synchronization.
本文档记录了本 Fork 为了支持 Vercel 部署及其他定制化功能而进行的修改。在与上游同步时，应保留这些修改。

## 1. Vercel Configuration (Vercel 配置)

### `vercel.json`
- **Purpose**: Defines Vercel build configuration, rewrites, and serverless function settings.
- **Key Settings**:
  - Rewrites `/api/(.*)` to `api/index.py`.
  - Configures build command for frontend (`cd frontend && pnpm install && pnpm build`).
  - Sets up Python runtime for backend.

### `api/index.py`
- **Purpose**: Entry point for Vercel Serverless Functions.
- **Modifications**: Adapts the Flask app to run in Vercel's serverless environment. Imports `app` from `backend.app`.

### `requirements.txt`
- **Purpose**: Defines Python dependencies.
- **Modifications**: Ensures compatibility with Vercel's Python runtime. Includes packages that might be missing in `pyproject.toml` or `uv.lock` if Vercel doesn't support them directly (though modern Vercel might). Kept for safety.

## 2. Environment Configuration (环境变量配置)

### `backend/config.py`
- **Purpose**: Application configuration.
- **Modifications**:
  - Extensive use of `os.getenv()` to load settings from Environment Variables (critical for Vercel).
  - Support for `IMAGE_PROVIDERS_CONFIG_BASE64` and `IMAGE_PROVIDERS_CONFIG` env vars to inject YAML config without physical files.
  - Added `STORAGE_BACKEND` support.
  - Preserved `GOOGLE_CLOUD_API_KEY` and other custom env vars.
  - Merged with Upstream's `reload_config`, `load_text_providers_config` and validation logic.

### `.env.example`
- **Purpose**: Template for environment variables.
- **Modifications**: Includes Vercel-specific and custom variables not present in upstream.

## 3. Storage Abstraction (存储抽象)

### `backend/utils/storage.py`
- **Purpose**: Abstract storage backend (Local, Vercel Blob, Vercel KV).
- **Modifications**: This file does not exist in upstream. It allows the app to store generated images in cloud storage when running on Vercel (where local filesystem is ephemeral).

## 4. Documentation (文档)

### `README.md`, `README.zh.md`, `README_en.md`
- **Modifications**:
  - Multi-language support structure.
  - Added "Upstream Sync" section.
  - Added Vercel Deployment guide.

### `scripts/sync_upstream.sh`
- **Purpose**: Automation script for syncing with upstream while preserving these customizations.

## Future Sync Guide (未来同步指南)

When running `./scripts/sync_upstream.sh`, please pay attention to conflicts in the files listed above.
- **Always Accept User's Version (Ours)** for: `vercel.json`, `api/index.py`, `backend/utils/storage.py`.
- **Merge Carefully** for: `backend/config.py`, `.gitignore`, `README.md`.
- **Generally Accept Upstream (Theirs)** for: `backend/app.py` (unless Vercel entry point logic changes drastically), `frontend/src/*` (application logic).

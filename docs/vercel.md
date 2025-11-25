# Vercel 部署指南

本文档介绍如何将 RedInk 部署到 [Vercel](https://vercel.com/) 平台。

## 前置要求

- GitHub 账号
- Vercel 账号
- Python 3.11+ (用于本地开发和依赖导出)
- Node.js 18+ & pnpm (用于前端构建)
- uv (Python 包管理工具)

## 部署步骤

### 1. 准备项目

如果你还没有克隆项目，请先克隆：

```bash
git clone https://github.com/HisMax/RedInk.git
cd RedInk
```

### 2. 生成依赖文件

Vercel Python 运行时需要 standard `requirements.txt`。我们使用 `uv` 来生成它：

```bash
uv pip compile pyproject.toml -o requirements.txt
# 如果你使用 Redis/Vercel KV，请确保 redis 包也在其中（本项目已包含）
```

*注意：`requirements.txt` 已包含在项目中，如果你修改了 `pyproject.toml` 依赖，请重新生成。*

### 3. 配置文件说明

项目根目录包含 `vercel.json`，用于配置 Vercel 的构建和路由：

```json
{
  "version": 2,
  "builds": [
    { "src": "api/index.py", "use": "@vercel/python" },
    { "src": "frontend/package.json", "use": "@vercel/static-build", "config": { "distDir": "dist" } }
  ],
  "rewrites": [
    { "source": "/api/(.*)", "destination": "/api/index.py" },
    { "source": "/(.*)", "destination": "/frontend/$1" }
  ]
}
```

- **api/index.py**: Python 后端的入口点。
- **frontend/package.json**: 前端静态构建配置。
- **rewrites**: 将 `/api/*` 请求转发给 Python 后端，其余请求转发给前端。

### 4. Vercel 项目设置

1. 登录 Vercel Dashboard。
2. 点击 **"Add New..."** -> **"Project"**。
3. 导入你的 GitHub 仓库。
4. 在 **Configure Project** 页面：
   - **Framework Preset**: 选择 `Vite` (Vercel 通常会自动检测)。
   - **Root Directory**: 保持默认 `.` (因为是 Monorepo 结构，我们在 vercel.json 中指定了构建路径)。
   - **Environment Variables**: 配置环境变量（见下文）。

### 5. 环境变量配置

在 Vercel 项目设置中添加以下环境变量：

| 变量名 | 必填 | 说明 | 示例 |
|--------|------|------|------|
| `GOOGLE_CLOUD_API_KEY` | 是 | Google Gemini API Key | `AIzaSy...` |
| `IMAGE_PROVIDER` | 否 | 图片生成服务商 | `google_genai` 或 `image_api` |
| `IMAGE_API_KEY` | 否 | 图片服务商 API Key | `sk-...` |
| `TEXT_API_KEY` | 否 | 文本生成 API Key (如需) | `sk-...` |
| `TEXT_API_BASE_URL` | 否 | 文本生成 API Base URL | `https://api.openai.com/v1` |
| `STORAGE_BACKEND` | 是 | 存储后端类型 | `vercel-kv` |
| `KV_URL` (或 `REDIS_URL`) | 是 | Vercel KV / Redis 连接串 | `redis://...` |

**注意：** 默认的文件存储是本地文件系统，在 Vercel Serverless 环境中是临时的（会丢失）。为了持久化保存生成历史和图片，必须配置 `STORAGE_BACKEND=vercel-kv` 并绑定 Vercel KV 数据库。

### 6. 配置存储 (Vercel KV)

为了持久化数据（历史记录和生成的图片），请使用 Vercel KV (Redis)：

1. 在 Vercel 项目 Dashboard 点击 **Storage** 选项卡。
2. 点击 **Create Database** -> **KV (Redis)**。
3. 创建后，将其连接到你的项目。
4. Vercel 会自动添加 `KV_URL`, `KV_REST_API_URL` 等环境变量。
5. 确保在环境变量中设置 `STORAGE_BACKEND` 为 `vercel-kv`。

*提示：图片数据将作为二进制字符串存储在 Redis 中。对于生产环境，建议根据图片大小和数量评估 Redis 容量成本。*

### 7. 部署

#### 关于 `image_providers.yaml`
默认情况下 `image_providers.yaml` 被 git 忽略。
- 如果你使用默认的 **Google GenAI**，无需此文件（代码有内置默认配置）。
- 如果你使用 **Custom Image API** 或其他服务商，你需要配置此文件并将其**提交到仓库**（请确保其中不包含直接的 API Key，而是引用环境变量），或者修改 `.gitignore` 允许提交它。

点击 **Deploy** 按钮。等待构建完成。

访问分配的域名（例如 `redink.vercel.app`）。

## 验证与测试

### 本地测试 (Vercel CLI)

你可以使用 Vercel CLI 在本地模拟生产环境：

```bash
npm i -g vercel
vercel dev
```

访问 `http://localhost:3000` 进行测试。

### 线上验证

1. **健康检查**: 访问 `/api/health`，应返回 JSON 状态。
2. **生成测试**: 在首页输入主题，测试大纲生成和图片生成。
   - 观察生成进度条（SSE 流式传输）。
   - 图片生成成功后，点击图片查看大预览。
3. **持久化测试**: 刷新页面，查看历史记录是否保留。

## 故障排除

### Serverless Function Timeouts (超时)
Vercel Hobby 计划的 Serverless Function 超时时间为 10 秒（Pro 为 60 秒或更长）。
- **现象**: 图片生成过程中请求断开或报错 504 Gateway Timeout。
- **解决**: 
  - 升级到 Pro 计划。
  - 或者使用更快的图片生成模型。
  - 我们的前端使用 SSE (Server-Sent Events) 接收进度，后端应确保持续发送数据以保持连接活跃，但硬性执行时间限制仍然存在。

### Python 依赖问题
如果部署失败报错 `ModuleNotFoundError`，请检查 `requirements.txt` 是否包含所有依赖，并且版本兼容。

### 存储限制
Vercel KV (Upstash) 有请求大小和存储限制。如果生成的图片过大（超过几 MB），写入 Redis 可能会失败或变慢。建议在 `image_providers.yaml` 或代码中配置图片压缩（已内置）或减小分辨率。

---

如有其他问题，请查阅 [Vercel 文档](https://vercel.com/docs)。

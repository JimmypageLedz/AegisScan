# AegisScan Backend

这是 AegisScan 的后端服务，负责资产管理、扫描任务调度、安全检测、风险发现存储和 LLM 报告生成。

后端采用 FastAPI 提供 REST API，使用 SQLAlchemy 操作 SQLite 数据库，并通过 Redis + Celery 执行异步扫描任务。

## 功能模块

- Assets：管理待扫描目标，包括创建、查询和删除资产。
- Tasks：创建扫描任务，记录任务状态，并触发 Celery 后台扫描。
- Findings：保存扫描器发现的安全配置问题，并支持按任务查询。
- Reports：根据指定任务的 Findings 生成风险报告。
- LLM：支持 mock 模式和真实 OpenAI-compatible API 调用，也支持读取本地 Codex/CCSwitch 风格配置。
- Scanners：包含可达性、安全响应头、Cookie、CSP 和 CORS 检测逻辑。

## 技术栈

- FastAPI：后端 Web 框架和接口文档。
- SQLAlchemy：ORM 和数据库访问。
- SQLite：本地开发数据库。
- Pydantic：请求和响应数据校验。
- httpx：发送 HTTP 请求并分析目标站点响应。
- Redis：Celery 消息队列。
- Celery：异步任务执行。

## 目录结构

```text
app/
  api/          API 路由
  core/         通用异常和日志配置
  models/       SQLAlchemy 数据模型
  schemas/      Pydantic Schema
  scanners/     安全扫描器
  services/     报告和 LLM 服务
  tasks/        Celery 任务
  celery_app.py Celery 应用入口
  config.py     配置加载
  db.py         数据库连接
  main.py       FastAPI 应用入口
```

## 本地启动

### 1. 安装依赖

```powershell
cd E:\web-security-platform\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

### 2. 启动 Redis

```powershell
docker run -d --name aegisscan-redis -p 6379:6379 redis:7
```

如果容器已经创建过：

```powershell
docker start aegisscan-redis
```

### 3. 启动 Celery Worker

```powershell
cd E:\web-security-platform\backend
.\.venv\Scripts\Activate.ps1
python -m celery -A app.celery_app:celery_app worker --loglevel=info --pool=solo
```

### 4. 启动 FastAPI

```powershell
cd E:\web-security-platform\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

启动后访问：

```text
http://127.0.0.1:8000/docs
```

## Docker 启动

也可以在项目根目录使用 Docker Compose：

```powershell
cd E:\web-security-platform
docker compose up --build
```

该方式会同时启动 API、Celery Worker 和 Redis。

## 环境变量

后端配置参考 `.env.example`：

```env
DATABASE_URL=sqlite:///./aegisscan.db
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
OPENAI_API_KEY=
OPENAI_BASE_URL=
OPENAI_MODEL=
LLM_MODE=mock
```

说明：

- `LLM_MODE=mock`：不调用真实模型，直接生成模拟报告，适合本地联调。
- `LLM_MODE=real`：调用 OpenAI-compatible API 生成真实报告。
- `.env` 不应提交到 Git，公开仓库只保留 `.env.example`。

## 主要接口

- `GET /health`：健康检查。
- `POST /assets`：创建资产。
- `GET /assets`：查看资产列表。
- `DELETE /assets/{asset_id}`：删除资产。
- `POST /tasks`：创建扫描任务。
- `GET /tasks`：查看任务列表。
- `DELETE /tasks/{task_id}`：删除任务。
- `GET /findings`：查看所有发现，可按 `task_id` 过滤。
- `DELETE /findings/{finding_id}`：删除发现。
- `POST /reports/{task_id}/generate`：为指定任务生成风险报告。
- `GET /reports`：查看报告列表。
- `DELETE /reports/{report_id}`：删除报告。
- `GET /llm/models`：获取可用模型列表。

## 扫描能力

- Alive：检测目标是否可访问，并记录异常状态码。
- Headers：检查 HSTS、X-Frame-Options、X-Content-Type-Options、Referrer-Policy 等安全响应头。
- Cookie：检查 Cookie 是否缺少 Secure、HttpOnly、SameSite 等属性。
- CSP：检查 Content-Security-Policy 是否缺失或配置过宽。
- CORS：检测是否反射任意 Origin，以及是否对不可信 Origin 开启 Credentials。

## 注意事项

扫描结果用于辅助发现 Web 安全配置风险，需要结合业务场景判断实际影响。本项目当前聚焦 HTTP 层面的配置检查，不等同于完整渗透测试工具。

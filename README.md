# AegisScan

AegisScan 是一个面向 Web 站点的安全配置扫描平台。项目提供资产管理、异步扫描任务、漏洞发现记录、风险报告生成和前端可视化操作界面，主要用于检查目标站点在 HTTP 响应头、Cookie、CSP、CORS 等方面的常见安全配置问题。

## 核心功能

- 资产管理：支持添加、查看和删除待扫描的目标站点。
- 异步扫描：使用 Redis 和 Celery 执行后台扫描任务，避免接口请求长时间阻塞。
- 安全检测：支持站点可达性、安全响应头、Cookie 属性、Content-Security-Policy、CORS 配置等检查。
- 发现记录：扫描结果会保存为 Finding，并支持按任务查看对应风险点。
- 报告生成：支持 mock 模式和真实 LLM 模式，根据扫描发现生成中文风险分析报告。
- 模型配置：前端可配置 LLM Base URL、API Key，并支持获取模型列表后选择模型。
- 可视化前端：提供资产、任务、发现、报告和模型设置等操作入口。
- 容器化部署：提供 Dockerfile 和 docker-compose.yml，可启动 API、Worker 和 Redis。

## 技术栈

- 后端：FastAPI、SQLAlchemy、Pydantic、SQLite、httpx
- 异步任务：Redis、Celery
- 前端：React、TypeScript、Vite
- LLM 接入：OpenAI-compatible API
- 容器化：Docker、Docker Compose

## 项目结构

```text
backend/
  app/
    api/          FastAPI 路由
    models/       SQLAlchemy 数据模型
    schemas/      Pydantic 请求/响应模型
    scanners/     安全扫描模块
    services/     报告生成和 LLM 调用逻辑
    tasks/        Celery 后台任务
frontend/
  src/            React 前端源码
docker-compose.yml
```

## 本地启动

### 启动后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

后端接口文档：

```text
http://127.0.0.1:8000/docs
```

### 启动 Redis

```powershell
docker run -d --name aegisscan-redis -p 6379:6379 redis:7
```

如果容器已经存在，可以使用：

```powershell
docker start aegisscan-redis
```

### 启动 Celery Worker

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m celery -A app.celery_app:celery_app worker --loglevel=info --pool=solo
```

### 启动前端

```powershell
cd frontend
npm install
npm run dev
```

前端地址：

```text
http://localhost:5173
```

## Docker 启动

在项目根目录执行：

```powershell
docker compose up --build
```

该命令会启动 FastAPI 后端、Celery Worker 和 Redis。

## LLM 配置

后端优先读取 `backend/.env` 中的配置：

```env
OPENAI_API_KEY=
OPENAI_BASE_URL=
OPENAI_MODEL=
LLM_MODE=mock
```

当 `LLM_MODE=mock` 时，系统会生成本地模拟报告，方便无 API Key 的情况下测试完整流程。

当 `LLM_MODE=real` 时，系统会调用 OpenAI-compatible 接口生成真实风险报告。如果 `.env` 中没有配置完整的 LLM 信息，后端会尝试读取本机 Codex/CCSwitch 风格的配置文件。

## 使用流程

1. 在前端新增一个资产，填写名称和目标 URL。
2. 对资产创建扫描任务。
3. Celery Worker 在后台执行扫描器。
4. 扫描结果写入数据库，形成 Findings。
5. 在前端查看指定任务的扫描发现。
6. 根据 Findings 生成风险报告。
7. 根据需要删除资产、任务、发现或报告。

## 当前扫描能力

- Alive 检测：判断目标是否可访问，并记录异常状态码。
- Headers 检测：检查 HSTS、X-Frame-Options、X-Content-Type-Options、Referrer-Policy 等响应头。
- Cookie 检测：检查 Cookie 是否缺少 Secure、HttpOnly、SameSite 等属性。
- CSP 检测：检查 Content-Security-Policy 是否缺失或配置过宽。
- CORS 检测：检测是否反射任意 Origin、是否对不可信 Origin 开启 Credentials。

## 说明

本项目定位为 Web 安全配置扫描和风险报告生成平台，主要关注 HTTP 层面的安全配置问题。扫描结果需要结合业务场景判断风险等级，不能直接等同于完整的渗透测试结论。

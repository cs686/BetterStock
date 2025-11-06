# BetterStock 财经新闻聚合与量化选股平台

BetterStock 是一个整合了新闻异步采集、行情展示、基于大模型的情感分析、行业 Z-score 因子和回测能力的端到端解决方案。本版本完成了项目路线中「MVP」与「版本升级」两个阶段的能力。

## 功能概览

### MVP 能力
- ✅ **异步新闻爬虫**：使用 `aiohttp`+RSS/HTML 抓取主流财经网站，并支持定时刷新。
- ✅ **实时行情展示**：封装市场数据接口，优先使用 AKShare，无法连接时自动切换为本地 mock 数据。
- ✅ **新闻情感分析**：封装大模型接口，可配置 OpenAI，也提供启发式兜底，支持批量分析。
- ✅ **综合选股打分**：结合情绪、行业热度、技术面、基本面四类因子进行加权评分。

### 版本升级能力
- ✅ **行业 Z-score 模块**：滚动窗口标准化行业指标，识别行业景气度异常。
- ✅ **回测系统与报告**：基于得分构建组合，计算收益、回撤、夏普等指标并输出交易记录。

## 后端服务

- 技术栈：FastAPI + SQLAlchemy + APScheduler。
- 目录：`backend/app`
  - `services/`：爬虫、行情、情感、评分、Z-score、回测等核心服务。
  - `routers/`：API 路由，包含新闻、行情、分析、回测四大模块。
  - `tasks/`：调度与数据库初始化。
- 启动步骤：
  ```bash
  cd backend
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  uvicorn app.main:app --reload
  ```
- 可选：设置 `BETTERSTOCK_LLM_PROVIDER=openai` 并配置 `OPENAI_API_KEY`，即可使用大模型进行情感分析。

## 前端应用

- 技术栈：Vite + Vue 3 + Axios。
- 目录：`frontend`
  - `App.vue` 提供四块仪表盘：行情、新闻、评分、回测。
  - 通过 `/api/*` 代理访问后端。
- 启动步骤：
  ```bash
  cd frontend
  npm install
  npm run dev
  ```

## 关键 API

| 接口 | 描述 |
| ---- | ---- |
| `POST /news/refresh` | 异步抓取最新新闻并进行情感分析 |
| `GET /news/latest` | 获取已存储的新闻及情感结果 |
| `GET /market/quotes` | 拉取市场实时行情 |
| `GET /analytics/scores` | 返回标准化后的综合评分结果 |
| `POST /analytics/industry/zscore` | 计算行业 Z-score 并持久化 |
| `POST /backtest/run` | 基于最新得分执行快速回测 |

## 数据与扩展

- 默认使用 SQLite，生产环境可替换为 MySQL/PostgreSQL。
- 市场数据、情感分析均提供接口化封装，便于替换为企业内部数据源或大模型平台。
- 回测模块以 Pandas 为核心，后续可扩展为 RQAlpha、Backtrader 等更完整引擎。

## 开发规划

- 下一阶段将增加自动化回测报告生成、实时推送以及多因子模型的在线训练部署。


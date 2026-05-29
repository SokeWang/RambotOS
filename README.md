# 🌌 RambotOS - 现代化纯净前后端分离 AI 智能管家操作系统 / Modern Decoupled Headless AI Butler OS

[**中文说明**](#-rambotos---%E7%8E%B0%E4%BB%A3%E5%8C%96%E7%BA%AF%E5%87%80%E5%89%8D%E5%90%8E%E7%AB%AF%E5%88%86%E7%A6%BB-ai-%E6%99%BA%E8%83%BD%E7%AE%A1%E5%AE%B6%E6%93%8D%E4%BD%9C%E7%B3%BB%E7%BB%9F) | [**English README**](#-rambotos---modern-decoupled-headless-ai-butler-os)

---

# 🌌 RambotOS - 现代化纯净前后端分离 AI 智能管家操作系统

> **RambotOS** 是一款先进、模块化、高内聚的个人 AI 智能管家操作系统框架。作为一个幽默风趣、极简且无感贴心的电子管家，RambotOS 深度集成了大语言模型多轮对话、多模态感知、双轨长期记忆（SQLite + ChromaDB 向量检索）、多渠道主动式后台服务监听（Email 邮件 & Telegram 机器人）以及插件化技能扩展系统，为您提供沉浸式的智能助理体验。

---

## 🎨 核心设计理念与视觉美学

RambotOS 遵循现代化的 Web 设计规范与极致的前后端分离架构，移除了笨重的桌面客户端依赖，拥抱纯粹的 Web 体验：
*   **极致视觉美学**：前端基于 React + Vite + Tailwind CSS 精心雕琢，使用和谐温润的 HSL 配色方案与现代玻璃微光质感（Glassmorphism），搭配丝滑的微交互动画，带来无与伦比的视觉冲击力。
*   **100% 纯净 headless 后端**：彻底剥离了 PySide6 / Qt 桌面 GUI 框架及图形库依赖，后端整体蜕变为纯粹的命令行常驻服务，极速响应，支持无头服务器部署。
*   **安全凭证隔离**：将 API Key、Bot Token 等敏感信息彻底抽离至本地 `.env` 环境变量配置文件中，受 Git 规则严密保护，永无凭证泄露之忧。

---

## 🏗️ 系统架构设计与进程编排

RambotOS 采用高内聚、低耦合的分层架构。系统的启动与生命周期由统一的 Python 进程调度中心 `launcher.py` 进行精细编排：

```mermaid
graph TD
    User[用户终端] -->|启动后端| Launcher[launcher.py 进程调度中心]
    Launcher -->|1. 一键拉起| Core[rambot_core.py FastAPI核心接口]
    Core -->|心跳健康检查| Wait[等待 8000 端口激活]
    Wait -->|2. 分身拉起| TG[standalone_telegram.py TG机器人]
    Wait -->|2. 分身拉起| Mail[standalone_monitor.py 邮箱监听器]
    
    User -->|启动前端| Vite[Vite 开发者服务 :5173]
    Vite -->|Websocket / API| Core
    
    Launcher -->|Ctrl+C 级联终止| Cleanup[优雅清理所有子进程 0 僵尸进程残留]
```

### 🧱 核心组件分布
*   **AI 调度中枢 (FastAPI Core)**：负责全局聊天路由网关、多渠道会话统一映射、记忆动态提取与检索、技能热拔插发现以及实时优先级通知网关。
*   **Telegram 机器人分身 (Standalone Telegram)**：独立运行的 Telegram Bot 线程，负责与主人的 IM 会话交互，主动将消息映射并推送至 AI Core。
*   **邮箱智能管家 (Standalone Email)**：独立运行的邮件长轮询监听器，能够自动识别主人来信并代理拟写、发送回复。
*   **Web 客户端 (Vite React Frontend)**：精致的前端聊天与生成式 UI 交互画布。

---

## 🚀 核心技术突破

### 1. 🧠 统一会话映射与优先级通知网关
*   能够将来自 Vite Web 界面、邮件、Telegram 机器人的不同通信渠道账号动态关联至同一个统一会话中，并智能区分主人（Master）与访客（Guest）权限。
*   设计了基于线程安全双端队列（Deque）的通知网关，支持不同评级的警报消息实时推送到用户的 Web 界面。

### 2. ⚡ 层级化 Prompt 体系（Token 节省达 30%-40%）
系统 Prompt 采用运行时动态拼接设计，极大减少了初始上下文的 Token 浪费：
*   **核心身份层 (Core Identity)**：确立 Rambot 睿智、言简意赅且主动关怀的管家性格。
*   **技能发现层 (Skill Protocol)**：无需在启动时塞入所有技能说明，而是按需动态扫描并加载。
*   **记忆提取层 (Memory Protocol)**：动态织入当前会话相关的历史记忆碎片。
*   **Extended 交互层**：动态匹配并输出生成式 UI 协议与媒体指令。

### 3. ✂️ 上下文滑动裁剪中间件
通过 LangGraph 深度定制的 `trim_memory` 中间件，自动对长对话进行无感裁剪：
*   完美保留系统首轮 prompt 与核心指令。
*   自动平滑截断，仅保留最近 **5 轮 (Human ↔ AI)** 的活跃对话，防止上下文窗口膨胀和 API Token 的冗余消费。

### 4. 🧩 插件化热插拔技能库 (Skills Ecosystem)
所有高阶能力均作为独立插件存储于根目录的 `/skills` 文件夹下，拥有统一的 `SKILL.md` 规范。AI 在对话中遇到匹配任务时，会实时动态阅读对应 Markdown 来获取运行指令：
*   `agentmail`：自主代发代收的邮件机器人。
*   `algorithm-engineer`：代码深度编写与架构分析。
*   `linkedin-job-automator`：简历自动投递与投递管道管理。
*   `resume-cv-builder`：ATS 友好的 PDF/HTML 简历自动生成器。
*   `spotify-controller`：系统媒体和播放列表控制器。
*   `stock-market`：实时股市行情分析。
*   `task-scheduler` & `time-service`：全局定时任务及日历管家（如“提醒喝水”、“早报简报”）。
*   `nano-banana` & `nano-veo`：底层驱动的图片及视频生成模型。

### 5. 💾 SQLite & ChromaDB 双轨长期记忆架构
*   **短期上下文安全检查**：由 LangGraph 的 SQLite checkpointer (`AsyncSqliteSaver`) 提供支持，确保多用户多线程历史会话的安全持久化。
*   **长期记忆事实检索**：AI 在交谈中会自动通过 `MemoryExtraction` 事实抽取模型提炼主人的偏好和设定，并将其写入本地的 **ChromaDB 向量数据库** 中，在后续对话中通过语义向量检索（Embedding）实时唤醒记忆。

### 6. 👂 纯净原生的 Perceptual 线程
*   **无 GUI 语音唤醒**：通过 `pvporcupine` 在后台运行低功耗唤醒监听，由纯 Python 的 `threading.Thread` 提供安全的多线程支持，彻底移除了对旧版 PySide 线程的依赖。
*   **极速本地 ASR**：基于 `Faster-Whisper` 实现本地毫秒级的高精语音转文字。
*   **流畅 TTS**：通过 `edge-tts` 调用微软神经网络语音，生成极具自然感的拟人声音输出。

---

## 📂 项目目录结构说明

```filepath
RambotOS/
├── launcher.py                # 统一进程守护与调度管理器 (核心启动入口)
├── rambot_core.py             # FastAPI 后端核心网关与 API 接口服务
├── standalone_telegram.py     # 独立 Telegram 机器人监听入口
├── standalone_monitor.py      # 独立 Email 邮件监听入口
├── backend/                   # 🚀 统一内聚后端源码包 (sys.path 动态注入)
│   ├── config/                # 系统中心化配置 (.env 环境变量解析)
│   ├── core/                  # AI 大脑核心 (Prompt/历史/ChromaDB/技能索引)
│   ├── agents/                # LangGraph 核心智能代理决策器
│   ├── services/              # 后台核心服务 (ASR/TTS/唤醒词/邮件/TG服务)
│   ├── tools/                 # Python 原生 Langchain 工具集
│   ├── tasks/                 # 定时调度后台任务
│   ├── db/                    # 本地持久化数据库存储 (SQLite/Chroma)
│   └── utils/                 # 公共工具库
├── frontend/                  # React + Vite + Tailwind CSS 前端网页源码
├── skills/                    # 可热插拔的 markdown 技能包
├── tests/                     # 历史与集成调试测试脚本
├── requirements.txt           # 清理 PySide6 后的纯净 Python 依赖包
├── .env                       # 本地凭证文件 (Git 自动忽略)
└── LICENSE                    # Apache 2.0 开源许可协议
```

---

## 🛠️ 快速安装与配置说明

### 1. 系统前置要求
*   建议使用 `Python 3.10+` 和 `Node.js 18+`。
*   对于高级 PDF/HTML 转换能力，推荐安装 `pandoc`：
    ```bash
    brew install pandoc
    ```

### 2. 后端虚拟环境与依赖安装
在项目根目录下创建 Python 虚拟环境并安装纯净的后端依赖：
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. 前端安装依赖
进入 `frontend` 文件夹并安装依赖：
```bash
cd frontend
npm install
cd ..
```

### 4. 凭证文件 `.env` 配置
在项目根目录下创建一个命名为 `.env` 的文件，填入您本地的 API 密钥及账号凭证（程序已配置 Git 忽略该文件，保证安全）：
```env
# Gemini LLM API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Picovoice 语音唤醒 Access Key
PICOVOICE_ACCESS_KEY=your_picovoice_key_here

# Telegram 机器人 Token 
TELEGRAM_TOKEN=your_telegram_bot_token_here

# 邮箱监听与代发凭证 (AgentMail 或者是您邮箱的 SMTP 授权码)
AGENTMAIL_API_KEY=your_agentmail_key_here
```

---

## 🚀 启动 RambotOS 智能管家

RambotOS 支持现代化的高效前后端分离开发与运行，您需要开启两个终端窗口：

### 第一步：启动常驻后端服务 suite
在项目根目录下，直接执行：
```bash
./.venv/bin/python launcher.py
```
> [!IMPORTANT]
> 此命令将一键在您的终端里拉起 **FastAPI 核心 (8000 端口)**、**Telegram 机器人** 和 **Email 监听分身**，前台会持续为您打印心跳与心率监测。
> 当您需要关闭时，**在终端中按下 `Ctrl + C` 即可 1 秒内优雅清理所有子进程，绝无端口占用**。

### 第二步：启动前端可视化网页
在另一个终端窗口中，进入前端工程并启动 Vite：
```bash
cd frontend
npm run dev
```
> [!TIP]
> 您的前端网页将运行在 `http://localhost:5173/`。它会自动链接本机的 `8000` 端口后端服务，开启流畅无比的网页智能管家体验！

---

# 🌌 RambotOS - Modern Decoupled Headless AI Butler OS

> **RambotOS** is an advanced, unified, and highly cohesive agentic AI operating system framework. Acting as a sophisticated, witty, and minimalist electronic butler, RambotOS integrates conversational LLMs, multimodal perception, dual-track long-term memory (SQLite + ChromaDB vector search), multi-channel background service monitoring (Email & Telegram), and a hot-pluggable skills extension engine, delivering a fully immersive desktop AI assistant experience.

---

## 🎨 Core Design Philosophy & Visual Aesthetics

RambotOS strictly follows modern web standards and an absolute frontend-backend separated architecture, discarding heavy desktop dependencies to embrace a pure web client experience:
*   **Premium Visual Aesthetics**: The frontend UI is meticulously crafted in React + Vite + Tailwind CSS, featuring a tailored dark-theme layout, subtle HSL gradients, and modern Glassmorphism backdrops combined with fluid micro-animations.
*   **100% Pure Headless Backend**: PySide6 and Qt framework dependencies have been entirely decoupled. The backend runs strictly as a clean terminal process manager, responsive and ready for headless server deployments.
*   **Credential Environment Isolation**: Sensitive keys (API Keys, Bot Tokens) are isolated in a local `.env` file, protected by Git exclusion filters, preventing accidental credentials leakage.

---

## 🏗️ System Architecture & Orchestration

RambotOS is designed with a cohesive multi-layered architecture. The backend services' lifecycles are orchestrated through a unified process manager `launcher.py`:

```mermaid
graph TD
    User[User Terminal] -->|Start Backend| Launcher[launcher.py Orchestrator]
    Launcher -->|1. Spawn Core| Core[rambot_core.py FastAPI Gateway]
    Core -->|Health Check| Wait[Wait for Port 8000 to be Active]
    Wait -->|2. Spawn Monitors| TG[standalone_telegram.py TG Bot]
    Wait -->|2. Spawn Monitors| Mail[standalone_monitor.py Email Monitor]
    
    User -->|Start Frontend| Vite[Vite Dev Server :5173]
    Vite -->|Websocket / API| Core
    
    Launcher -->|Ctrl+C Signals| Cleanup[Cascade Terminate all Workers: 0 Zombie Processes]
```

### 🧱 Component Breakdown
*   **Central Gateway Core (FastAPI Core)**: Exposes endpoints for gateway chat routing, monitor heartbeat registration, real-time priority notification queuing, skill index auto-loading, and semantic memory search.
*   **Telegram Bot Agent (Standalone Telegram)**: A background worker handle interacting with the user on IM channels, forwarding triggers seamlessly back to the FastAPI Core.
*   **Smart Email Butler (Standalone Email)**: An independent mail listener checking incoming mail, drafting responses autonomously, and replying on behalf of the user.
*   **Web Client (Vite React Frontend)**: An exquisite frontend chat terminal and generative UI interaction canvas.

---

## 🚀 Key Technical Highlights

### 1. 🧠 Unified Session Mapping & Priority Notification Gateway
*   Dynamically maps conversations originating from different communication channels (Web client, Email, Telegram bot) into a Unified Session, distinguishing Master and Guest privileges.
*   Features a thread-safe deque-based notification gateway to push real-time, priority-rated alerts directly onto the user's UI.

### 2. ⚡ Layered Prompt System (Token Savings up to 30%-40%)
The system prompt is assembled dynamically at runtime, dramatically reducing token overhead:
*   **Core Identity Layer**: Emphasizes Rambot's witty, concise, and proactive personality.
*   **Skill Protocol Layer**: Avoids listing all skill instructions at startup; instead, dynamically index them as needed.
*   **Memory Retrieval Layer**: Interweaves semantic facts from the vector store matching the current dialogue context.
*   **Extended Directives Layer**: Integrates Generative UI protocols and multimodal directives.

### 3. ✂️ Conversation Trimming Middleware
Leveraging LangGraph, a specialized `trim_memory` middleware handles sliding window compression:
*   Perfectly preserves initial system prompts and core instruction blocks.
*   Automatically trims older conversations, keeping only the **last 5 rounds (Human ↔ AI)** of the active history to save context tokens.

### 4. 🧩 Hot-Pluggable Skills Ecosystem
All advanced skills are pluggable, saved in `/skills` folders carrying a descriptive `SKILL.md` file. The AI dynamically discovers and reads these guidelines to fulfill tasks:
*   `agentmail`: Autonomous email manager replying to incoming mails.
*   `algorithm-engineer`: In-depth code generation and system analysis tool.
*   `linkedin-job-automator`: Intelligent job discovery and pipeline automation.
*   `resume-cv-builder`: ATS-optimized resume builder exporting to Markdown, HTML, or PDF.
*   `spotify-controller`: Controls media players and tracks.
*   `stock-market`: Real-time stock market quotes and analytics.
*   `task-scheduler` & `time-service`: Timer, calendar, and scheduled triggers (e.g., water reminders).
*   `nano-banana` & `nano-veo`: Native image and dialogue-synced video models.

### 5. 💾 SQLite & ChromaDB Dual-Memory Architecture
*   **Short-Term History**: Powered by LangGraph's SQLite saver (`AsyncSqliteSaver`), providing secure, multi-threaded conversational persistence.
*   **Long-Term Semantic Memory**: During conversations, the agent automatically extracts key facts about the user's setup and preferences via a `MemoryExtraction` model, saving them to a local **ChromaDB vector store** for semantic retrieval in future chats.

### 6. 👂 Pure Native Perceptual Threading
*   **Headless Voice Activation**: Continuously runs a low-power wake-word engine via `pvporcupine` using standard Python `threading.Thread`, fully replacing the legacy PySide6 `QThread` mechanisms.
*   **Speedy Local ASR**: Millisecond-level local speech-to-text transcriptions powered by `Faster-Whisper`.
*   **Fluid Neural TTS**: Conversational voice responses using Microsoft's neural `edge-tts`, delivering natural voice generation.

---

## 📂 Project Directory Structure

```filepath
RambotOS/
├── launcher.py                # Process scheduler & monitor daemon (Main Entrance)
├── rambot_core.py             # FastAPI Core & API Gateway Service
├── standalone_telegram.py     # Standalone Telegram Bot worker
├── standalone_monitor.py      # Standalone Email Monitor worker
├── backend/                   # 🚀 Unified backend code package (sys.path injected)
│   ├── config/                # System configuration & .env credentials parser
│   ├── core/                  # Prompt builders, histories, ChromaDB managers
│   ├── agents/                # LangGraph agents & tools manager
│   ├── services/              # ASR, TTS, wakewords, mail, and TG services
│   ├── tools/                 # Native Python Langchain tool suites
│   ├── tasks/                 # Task schedulers & automated cron jobs
│   ├── db/                    # Local persistent storages (SQLite & Chroma)
│   └── utils/                 # Public utils
├── frontend/                  # React + Vite + Tailwind CSS Frontend UI source
├── skills/                    # Pluggable skill guidelines (SKILL.md)
├── tests/                     # Historic testing and integration scripts
├── requirements.txt           # Pure backend dependencies (PySide6 decoupled)
├── .env                       # Local secrets template (Git ignored)
└── LICENSE                    # Apache 2.0 License
```

---

## 🛠️ Setup & Installation Guide

### 1. Prerequisites
*   `Python 3.10+` and `Node.js 18+` are required.
*   `pandoc` is highly recommended for document building tools:
    ```bash
    brew install pandoc
    ```

### 2. Python Environment Setup
Create a virtual environment and install the dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Frontend Setup
Install npm packages inside the `frontend` folder:
```bash
cd frontend
npm install
cd ..
```

### 4. Credential Config `.env`
Create a `.env` file at the project root and fill in your keys (fully protected by Git exclusion filters):
```env
# Gemini LLM API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Picovoice Wake-word Access Key
PICOVOICE_ACCESS_KEY=your_picovoice_key_here

# Telegram Bot Token 
TELEGRAM_TOKEN=your_telegram_bot_token_here

# Email Auth (SMTP authorization code or AgentMail credentials)
AGENTMAIL_API_KEY=your_agentmail_key_here
```

---

## 🚀 Running RambotOS

RambotOS supports highly efficient frontend-backend separated startup. You need to open two terminal windows:

### Step 1: Start the Headless Backend Services
In your first terminal, run:
```bash
./.venv/bin/python launcher.py
```
> [!IMPORTANT]
> This command spawns the **FastAPI Core (Port 8000)**, **Telegram Bot**, and **Email Monitor** workers under a clean python supervisor.
> Press **`Ctrl + C`** in this terminal to gracefully terminate all child processes and release port 8000 instantly.

### Step 2: Start the Web UI Development Server
In your second terminal, navigate into the frontend folder and run the dev server:
```bash
cd frontend
npm run dev
```
> [!TIP]
> The Web UI will be active at `http://localhost:5173/` and will automatically link to the local backend at `http://localhost:8000/`. Enjoy your streamlined smart AI Butler system!

---

## 📄 License
This project is licensed under the Apache 2.0 License - see the [LICENSE](file:///Users/wangpeidong/Documents/RambotOS/LICENSE) file for details.
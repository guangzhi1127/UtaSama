# UtaSama Agent 开发学习总结

这份文档用于帮助初学者快速复盘当前项目已经建立的过程，并理解其中涉及的 Agent 开发知识点。它不是单纯的项目说明书，而是“我从零做一个可运行聊天 Agent 原型时，到底学了什么、每一部分为什么存在”的学习笔记。

当前项目已经形成了一个轻量级 Web Agent 原型：

- 后端使用 `FastAPI` 提供接口。
- 大模型使用 DeepSeek 的 OpenAI 兼容接口。
- 前端使用原生 `HTML + CSS + JavaScript` 做聊天页面。
- RAG 使用本地 Markdown 知识库做轻量检索。
- 记忆系统使用本地 JSON / JSONL 文件保存会话、摘要和长期记忆雏形。
- 多 Agent / Skills / MCP 目前先做成配置化框架，方便后续继续接真实能力。
- 桌宠目前是页内静态/半动态 MVP，不是独立桌面软件。

## 1. 当前项目是什么形态

目前它不是 `.exe` 软件，而是一个本地 Web 应用原型。

运行时由两部分组成：

- 后端服务：`http://127.0.0.1:8000`
- 前端页面：`http://127.0.0.1:4173`

也就是说，用户在浏览器里打开前端页面，输入消息；前端通过 `fetch` 把消息发给后端；后端把消息、系统提示词、RAG 知识、历史记忆拼起来，请求 DeepSeek 模型；模型返回结果后，后端再把回复、路由信息、桌宠状态返回给前端显示。

后续如果要做成真正的软件，可以再用：

- `Electron`：把 Web 前端 + 本地后端包装成桌面软件。
- `Tauri`：更轻量的桌面壳。
- `PyInstaller`：把 Python 后端打包，但前端体验仍需额外处理。

当前阶段优先做 Web 原型是合理的，因为学习成本低、调试方便、适合两周内落地。

## 2. 当前项目目录结构

核心目录如下：

```text
UtaSama/
├─ main.py                         # FastAPI 后端主文件
├─ requirements.txt                # Python 依赖
├─ README.md                       # 项目简要说明
├─ 项目书.md                       # 项目规划书
├─ Agent开发学习总结.md             # 当前这份学习总结
├─ frontend/
│  ├─ index.html                   # 前端页面结构
│  ├─ styles.css                   # 前端视觉样式
│  ├─ app.js                       # 前端交互逻辑和 fetch 请求
│  └─ assets/
│     ├─ uta-avatar.jpg            # 聊天头像
│     └─ pet-states/               # 页内桌宠状态图
├─ character/
│  ├─ uta-sama.persona.md          # 角色人设文档
│  └─ prompts/
│     ├─ main-agent.system.md      # 主 Agent 系统提示词
│     ├─ music-agent.system.md     # 音乐专项 Agent 提示词
│     ├─ image-agent.system.md     # 图像专项 Agent 提示词
│     └─ pet-agent.system.md       # 桌宠专项 Agent 提示词
├─ knowledge/
│  ├─ persona/                     # RAG 人设知识库
│  └─ world/                       # RAG 世界观知识库
├─ memory/
│  ├─ chat_history.jsonl           # 历史聊天记录
│  ├─ session_summaries.json       # 会话摘要
│  ├─ user_profile.json            # 用户画像雏形
│  └─ memories.jsonl               # 长期记忆雏形
└─ config/
   ├─ agents/registry.json         # 多 Agent 注册表
   ├─ skills/registry.example.json # Skills 注册表示例
   └─ mcp/providers.example.json   # MCP 服务配置示例
```

理解这个结构很重要：Agent 项目不是只有一个提示词，而是由后端接口、模型调用、提示词、人设资料、记忆、工具、前端交互共同组成。

## 3. 项目建立过程复盘

### 第一步：明确项目目标

最初的目标是做一个自定义人设的二次元美少女聊天助手 Agent，包括：

- 主聊天 Agent。
- 音乐、文生图、桌宠等专项子 Agent。
- 类似微信聊天框的前端页面。
- 预留自定义 MCP、Skills 和未来扩展子 Agent 的能力。
- 适合作为两周内能落地、能写进简历的实习项目。

这个目标后来被收敛成一个更适合初学者的 MVP：

- 先保证主聊天 Agent 能跑通。
- 先做静态/半动态页内桌宠。
- 音乐播放、文生图、真实 MCP 先做配置和接口预留，不急着接真实能力。

这是 Agent 项目里很重要的思路：先做“能闭环”的最小版本，再逐步增强能力。

### 第二步：建立项目书和角色设定

项目最开始先写了 `项目书.md`，明确：

- 项目定位。
- 目标用户。
- 功能模块。
- 技术栈。
- 开发阶段。
- 后续可扩展方向。

然后根据乌塔形象修改了人设部分，把角色风格设定为：

- 明亮灵动，有舞台少女感。
- 温柔、细腻、重视陪伴。
- 对歌声、梦想、幸福有强烈信念。
- 日常对话自然轻快，情绪话题更柔软认真。

这里学到的知识点是：系统提示词不是随便写一段“你是谁”，而是要把角色身份、语气、边界、回答原则拆开写清楚。

### 第三步：搭建 FastAPI 后端

后端主文件是 `main.py`。

当前后端主要提供这些接口：

```text
GET  /health
GET  /runtime/config
GET  /history/{session_id}
POST /chat
```

各接口作用：

- `/health`：检查后端是否运行。
- `/runtime/config`：给前端返回当前 Agent、Skills、MCP 配置。
- `/history/{session_id}`：读取某个会话的历史记录。
- `/chat`：接收用户消息，调用模型，返回回复。

这里学到的知识点是：

- `FastAPI` 用来快速写 HTTP API。
- `Pydantic` 用来定义请求数据结构。
- `CORS` 用来允许前端跨端口访问后端。
- `uvicorn` 或 `fastapi dev` 用来启动开发服务器。

### 第四步：接入 DeepSeek 模型

当前模型配置在 `main.py` 中：

```python
CHAT_MODEL = "deepseek-v4-flash"
```

后端使用 OpenAI 兼容 SDK 调用 DeepSeek。也就是说，代码写法接近 OpenAI SDK，但 `base_url` 指向 DeepSeek 的接口地址，并通过环境变量读取 API Key。

需要准备：

```powershell
$env:DEEPSEEK_API_KEY="你的 key"
```

这里学到的知识点是：

- 大模型本身不是 Agent，模型只是“生成回复的大脑”。
- Agent 需要在模型外面增加提示词、记忆、工具、路由和业务逻辑。
- OpenAI 兼容接口可以让不同模型供应商使用相似的代码方式接入。

### 第五步：搭建前端聊天页面

前端主要由三个文件组成：

```text
frontend/index.html
frontend/styles.css
frontend/app.js
```

它们分别负责：

- `index.html`：页面结构，比如聊天区、输入框、侧边栏、桌宠容器。
- `styles.css`：视觉样式，比如颜色、边框、头像、桌宠动画。
- `app.js`：交互逻辑，比如点击发送、调用后端、更新聊天列表、保存本地状态。

当前前端已经实现：

- 类微信聊天框的主对话区。
- 左右红白边框风格。
- 乌塔头像。
- Agent / Skills / MCP 配置展示区。
- 运行时调试面板。
- 页内桌宠显示和拖拽。
- 使用 `fetch` 把消息发给后端 `/chat`。

这里学到的知识点是：

- 前端页面本身不会自动拥有模型能力。
- 前端必须通过 HTTP 请求把用户消息发给后端。
- `fetch` 是浏览器里调用后端接口的常用方式。
- `localStorage` 可以保存本地 UI 状态，比如会话 ID、桌宠位置。

### 第六步：跑通前后端通信

当前项目的核心数据流是：

```text
用户输入
  ↓
frontend/app.js
  ↓ fetch POST /chat
main.py
  ↓ 拼接提示词、RAG、记忆、路由信息
DeepSeek 模型
  ↓
main.py 返回 JSON
  ↓
frontend/app.js 渲染聊天气泡和桌宠状态
```

前端发送给后端的数据大致包含：

```json
{
  "message": "用户输入的内容",
  "session_id": "当前会话 ID"
}
```

后端返回的数据大致包含：

```json
{
  "reply": "模型回复",
  "session_id": "当前会话 ID",
  "active_agent": "当前路由到的 Agent",
  "rag_used": true,
  "history_used": true,
  "pet_state": {
    "mood": "happy",
    "animationState": "sing",
    "voiceLine": "..."
  }
}
```

这里学到的知识点是：前后端联调时，不只要看页面有没有回复，还要看请求是否真的到了后端、后端是否返回了预期字段、前端是否正确渲染这些字段。

### 第七步：加入轻量 RAG

RAG 的全称是 Retrieval-Augmented Generation，意思是“检索增强生成”。

简单说：不要把所有设定都塞进系统提示词，而是先把世界观、人设、设定资料放到知识库里。用户提问时，后端先从知识库检索相关内容，再把相关资料一起发给模型，让模型依据资料回答。

当前项目的 RAG 资料放在：

```text
knowledge/persona/
knowledge/world/
```

当前后端大致流程是：

```text
读取 Markdown 文档
  ↓
根据用户问题做关键词评分
  ↓
选出最相关的几段资料
  ↓
拼进模型 messages
  ↓
要求模型优先依据知识库回答
```

这里学到的知识点是：

- RAG 不是让模型自动上网。
- 当前项目没有联网搜索能力，模型不会自己去网上查资料。
- 知识库写得简练是正常的，MVP 阶段重点是先跑通检索链路。
- 如果知识库没有写某段设定，模型可能会凭训练知识回答，所以需要在提示词里要求“不确定就说明知识库未提供”。

后续如果升级，可以把当前关键词检索换成：

- 向量数据库：`Chroma`、`FAISS`、`Milvus` 等。
- Embedding 模型：把文本转成向量再做相似度搜索。
- 文档分块：把长文档切成更小的 chunk，提高命中率。

### 第八步：加入历史对话和会话摘要

当前记忆相关文件在 `memory/`：

```text
memory/chat_history.jsonl
memory/session_summaries.json
memory/user_profile.json
memory/memories.jsonl
```

它们的定位不同：

- `chat_history.jsonl`：保存原始聊天记录。
- `session_summaries.json`：保存会话摘要，减少长对话时塞太多历史。
- `user_profile.json`：保存用户偏好、称呼、长期信息。
- `memories.jsonl`：保存长期记忆条目。

这里学到的知识点是：Agent 的“记忆”不是模型天然记住你，而是工程系统主动保存、检索、再注入上下文。

目前项目已经具备：

- 会话 ID。
- 历史消息写入。
- 最近历史消息读取。
- 会话摘要文件结构。
- 长期记忆文件结构。

后续还需要继续增强：

- 自动判断哪些信息值得写入长期记忆。
- 给长期记忆加标签和重要度。
- 在用户提问时检索相关长期记忆。
- 在前端提供“查看 / 删除记忆”的入口。

### 第九步：加入多 Agent 路由框架

当前 Agent 注册表在：

```text
config/agents/registry.json
```

目前有：

- `utasama-main`：主聊天 Agent。
- `music-agent`：音乐专项 Agent。
- `image-agent`：图像专项 Agent。
- `pet-agent`：桌宠专项 Agent。

当前路由方式是轻量关键词路由。例如用户提到：

- 歌单、音乐、播放，可能路由到 `music-agent`。
- 画图、头像、桌宠状态图，可能路由到 `image-agent`。
- 桌宠、互动、待机，可能路由到 `pet-agent`。
- 普通聊天，默认由 `utasama-main` 处理。

这里学到的知识点是：多 Agent 不一定一开始就要做复杂的“多个模型互相对话”。初学阶段可以先做“主 Agent + 路由 + 专项提示词 + 工具预留”。

这已经能体现工程能力：

- 角色职责拆分。
- 运行时配置化。
- 未来扩展不需要重写主流程。

### 第十步：预留 Skills 和 MCP

当前 Skills 示例在：

```text
config/skills/registry.example.json
```

当前 MCP 示例在：

```text
config/mcp/providers.example.json
```

它们目前还不是完整可执行能力，而是“注册表”和“接口规划”。

可以这样理解：

- Skill：Agent 可以调用的具体能力，比如播放音乐、生成图片、切换桌宠动画。
- MCP：让 Agent 连接外部资源或工具的协议，比如本地音乐库、素材库、数据库。

当前项目先把它们设计出来，是为了后续扩展时不用推倒重来。

这里学到的知识点是：Agent 项目里，工具能力最好先抽象成清晰的输入输出，而不是一开始就把所有逻辑写死在聊天函数里。

### 第十一步：制作页内桌宠 MVP

当前桌宠资源在：

```text
frontend/assets/pet-states/
```

已有状态：

```text
idle.png
happy.png
think.png
sing.png
alert.png
preview-sheet.jpg
```

前端根据后端返回的 `pet_state` 切换桌宠状态。

后端 `build_pet_state()` 会根据用户消息、模型回复和路由结果，返回类似：

```json
{
  "mood": "sunny",
  "animationState": "idle",
  "voiceLine": "我在这里陪你呀。",
  "gesture": "standby",
  "followUpHint": "可以继续聊天"
}
```

前端再根据 `animationState` 切换图片和 CSS 动画。

这里学到的知识点是：桌宠不是一开始就必须做成复杂桌面宠物。先做页内状态机，可以快速验证：

- Agent 是否能输出状态。
- 前端是否能根据状态变化。
- 用户是否能感受到陪伴感。

## 4. 本项目用到的核心技术栈

### 后端

- `Python`：主要开发语言。
- `FastAPI`：写后端 API。
- `Pydantic`：定义请求参数和数据校验。
- `Uvicorn / fastapi dev`：启动本地开发服务器。
- `OpenAI Python SDK`：用 OpenAI 兼容方式调用 DeepSeek。
- `JSON / JSONL / Markdown`：保存配置、知识库和记忆。

### 前端

- `HTML`：页面结构。
- `CSS`：页面样式和桌宠动画。
- `JavaScript`：页面交互逻辑。
- `fetch`：请求后端接口。
- `localStorage`：保存本地 UI 状态。

### Agent 相关

- `System Prompt`：定义角色、人设、回答规则。
- `RAG`：从本地知识库检索设定资料。
- `Memory`：保存历史对话、摘要和长期记忆。
- `Router`：根据用户意图选择主 Agent 或专项 Agent。
- `Skills`：预留可调用能力。
- `MCP`：预留外部工具/资源连接方式。

## 5. 初学者必须理解的 Agent 概念

### 5.1 模型不等于 Agent

大模型只负责根据上下文生成文本。

Agent 是在模型外面包了一层工程系统，通常包括：

```text
Agent = 模型 + 提示词 + 记忆 + 工具 + 检索 + 路由 + 前后端交互
```

如果只调用一次模型，那叫聊天接口；如果它能记忆、检索资料、调用工具、根据任务切换能力，才更接近 Agent。

### 5.2 系统提示词和 RAG 的区别

系统提示词适合写：

- 角色身份。
- 说话风格。
- 行为边界。
- 回答原则。

RAG 适合放：

- 世界观资料。
- 人物关系。
- 能力设定。
- 项目文档。
- 经常需要查证的知识。

不要把所有设定都塞进系统提示词。提示词太长会难维护，也不利于后续扩展。

### 5.3 短期记忆和长期记忆的区别

短期记忆：

- 最近几轮聊天。
- 用来保持上下文连贯。
- 通常每次请求都带上最近 N 条。

长期记忆：

- 用户长期偏好。
- 重要事实。
- 角色关系。
- 需要跨会话保存的信息。

会话摘要：

- 用来压缩很长的聊天历史。
- 避免每次都把所有历史消息发给模型。

### 5.4 Skills 和 MCP 的区别

Skill 更像“一个具体能力”：

```text
播放音乐、生成图片、保存素材、切换桌宠动画
```

MCP 更像“连接外部工具或资源的标准接口”：

```text
本地音乐库、文件系统、数据库、素材管理服务
```

简单理解：

- Skill 解决“Agent 会做什么”。
- MCP 解决“Agent 怎么连接外部世界”。

### 5.5 前端不是 Agent，前端是交互入口

前端负责：

- 展示聊天消息。
- 收集用户输入。
- 展示 Agent 状态。
- 展示桌宠状态。
- 调用后端接口。

真正的 Agent 逻辑主要在后端：

- 调模型。
- 检索 RAG。
- 读取记忆。
- 路由子 Agent。
- 生成结构化状态。

## 6. 如何运行当前项目

### 6.1 创建虚拟环境

```powershell
python -m venv .venv
```

如果 PowerShell 禁止激活脚本，可以临时放开当前窗口权限：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

然后激活虚拟环境：

```powershell
.\.venv\Scripts\Activate.ps1
```

### 6.2 安装依赖

```powershell
python -m pip install -r requirements.txt
```

### 6.3 配置 DeepSeek Key

```powershell
$env:DEEPSEEK_API_KEY="你的 DeepSeek API Key"
```

注意：这个命令只对当前 PowerShell 窗口有效。重新打开终端后需要重新设置，或者之后再学习使用 `.env` 文件管理环境变量。

### 6.4 启动后端

```powershell
fastapi dev main.py
```

或者：

```powershell
uvicorn main:app --reload
```

看到类似下面的地址，说明后端启动成功：

```text
http://127.0.0.1:8000
```

可以打开：

```text
http://127.0.0.1:8000/docs
```

这个页面是 FastAPI 自动生成的接口文档。

### 6.5 启动前端

另开一个 PowerShell 窗口，在项目根目录运行：

```powershell
python -m http.server 4173 -d frontend
```

然后打开：

```text
http://127.0.0.1:4173/
```

## 7. 当前项目如何验收

### 7.1 后端是否运行

打开：

```text
http://127.0.0.1:8000/health
```

如果返回正常 JSON，说明后端在线。

### 7.2 接口文档是否可用

打开：

```text
http://127.0.0.1:8000/docs
```

能看到 `/chat`、`/runtime/config`、`/history/{session_id}` 就说明 FastAPI 路由正常。

### 7.3 前端是否能打开

打开：

```text
http://127.0.0.1:4173/
```

能看到聊天页面、头像、桌宠和配置区，说明前端静态页面正常。

### 7.4 消息是否传到后端

在前端发送一条消息，比如：

```text
你好，今天想聊聊音乐
```

如果后端终端出现请求日志，前端收到回复，说明前后端通信成功。

### 7.5 RAG 是否可能被调用

可以问：

```text
介绍一下乌塔的人设和说话风格
```

如果返回结果贴合 `knowledge/persona/` 里的设定，并且调试信息中 `rag_used` 为 true，就说明轻量 RAG 生效。

### 7.6 记忆是否写入

发送几条消息后，查看：

```text
memory/chat_history.jsonl
```

如果里面新增了用户和助手消息，说明历史记录已经写入。

### 7.7 桌宠是否切换状态

可以测试：

```text
帮我整理一个桌宠状态图提示词
```

预期效果：

- 路由可能命中图像或桌宠相关 Agent。
- 桌宠切换到思考或相关状态。
- 页面右下角桌宠气泡更新。

也可以测试：

```text
给我一组适合开心时听的歌单
```

预期桌宠可能进入唱歌状态。

## 8. 适合写进简历的项目亮点

可以这样概括当前项目：

```text
基于 FastAPI + DeepSeek API 构建了一个二次元角色陪伴型聊天 Agent 原型，
实现了前后端分离聊天页面、角色系统提示词、轻量 RAG 知识库检索、
会话历史存储、多 Agent 路由框架、Skills/MCP 扩展注册表和页内桌宠状态联动。
```

更工程化一点可以写：

- 使用 `FastAPI` 搭建大模型应用后端，封装 `/chat`、`/history`、`/runtime/config` 等接口。
- 使用 OpenAI 兼容 SDK 接入 DeepSeek 模型，实现角色化对话回复。
- 设计本地 Markdown RAG 知识库，将人设、世界观和长期记忆注入模型上下文。
- 使用 JSON / JSONL 实现轻量会话历史、摘要和长期记忆存储雏形。
- 设计多 Agent 注册表，支持主 Agent 与音乐、图像、桌宠专项 Agent 的路由分发。
- 使用原生 HTML/CSS/JS 实现聊天 UI、运行时调试面板和页内桌宠状态联动。

## 9. 当前未完成但已经预留的方向

下面这些不是失败，而是后续升级方向：

- 真实音乐播放 Skill：目前只有配置和路由预留，还没有真正播放本地音乐。
- 真实文生图 Skill：目前先生成/使用静态素材，还没有接入图像生成 API。
- 真正 MCP Server：目前只有配置示例，还没有启动独立 MCP 服务。
- 向量数据库 RAG：当前是轻量关键词检索，后续可以升级为 Embedding + Chroma/FAISS。
- 长期记忆抽取：当前有文件结构，后续需要做自动提取、去重、删除和可视化管理。
- 桌面级桌宠：当前是网页内桌宠，后续可以用 Electron/Tauri 做独立桌宠窗口。
- 用户认证和部署：当前是本地开发原型，还没有登录、权限和云端部署。

## 10. 建议的后续学习顺序

如果你是初学者，建议按下面顺序继续学，不要一口气追求全功能。

### 第 1 阶段：吃透当前前后端通信

重点理解：

- `frontend/app.js` 如何发送 `fetch`。
- `main.py` 的 `/chat` 如何接收请求。
- 后端返回的 JSON 如何被前端渲染。

验收目标：

- 能自己解释“一条消息从输入框到模型回复再回到页面”的完整路径。

### 第 2 阶段：吃透提示词和角色设定

重点理解：

- `SYSTEM_PROMPT`。
- `character/uta-sama.persona.md`。
- `character/prompts/main-agent.system.md`。

验收目标：

- 能修改角色语气，并观察回复风格变化。
- 能说明哪些内容适合放系统提示词，哪些适合放 RAG。

### 第 3 阶段：吃透轻量 RAG

重点理解：

- `knowledge/persona/`。
- `knowledge/world/`。
- `build_rag_context()`。
- `retrieve_persona_docs()`。
- `retrieve_world_docs()`。

验收目标：

- 新增一篇知识库文档。
- 提问后能看到模型使用新资料回答。

### 第 4 阶段：吃透历史记忆

重点理解：

- `session_id`。
- `chat_history.jsonl`。
- `session_summaries.json`。
- 最近历史和摘要如何拼进模型请求。

验收目标：

- 模型能记住当前会话前几轮内容。
- 长对话后能生成或使用摘要。

### 第 5 阶段：吃透多 Agent 路由

重点理解：

- `config/agents/registry.json`。
- `detect_route()`。
- `build_specialist_route_context()`。

验收目标：

- 输入音乐相关内容时命中音乐 Agent。
- 输入图像相关内容时命中图像 Agent。
- 输入桌宠相关内容时命中桌宠 Agent。
- 前端调试面板能显示路由结果。

### 第 6 阶段：做一个真正可执行 Skill

建议先做最简单的：

```text
桌宠状态切换 Skill
```

不要一开始就接复杂文生图。可以先让 Skill 根据输入返回：

```json
{
  "animationState": "happy",
  "voiceLine": "我听到啦，今天也一起加油呀。"
}
```

验收目标：

- 后端可以调用一个独立函数生成桌宠状态。
- 前端根据结果切换桌宠。
- Skill 输入输出结构清晰。

## 11. 两周内适合完成的 MVP 目标

如果目标是找实习或兼职，建议两周内把项目收敛到：

- 一个稳定可运行的聊天 Agent。
- 一个清晰的角色人设系统。
- 一个可解释的轻量 RAG。
- 一个可展示的记忆系统。
- 一个可视化前端页面。
- 一个页内桌宠联动效果。
- 一个预留好的 Agent / Skills / MCP 扩展框架。
- 一份 README 和项目书。

不要在两周内强行追求：

- 完整桌面宠物。
- 完整音乐播放器。
- 完整文生图平台。
- 复杂多 Agent 协作。
- 云端部署和登录系统。

先把主链路做扎实，更容易吃透，也更适合面试时讲清楚。

## 12. 面试时可以怎么讲这个项目

可以按这个顺序讲：

1. 我做的是一个角色陪伴型聊天 Agent，不是简单调用模型接口。
2. 我用 FastAPI 做后端，用原生前端做聊天页面。
3. 后端会把系统提示词、RAG 知识库、历史会话和用户输入组合后发给模型。
4. 我把人设和世界观拆成 Markdown 知识库，用轻量检索方式注入上下文。
5. 我设计了多 Agent 注册表，主 Agent 可以根据关键词路由到音乐、图像、桌宠专项 Agent。
6. 我预留了 Skills 和 MCP 配置，方便以后接入真实工具。
7. 我做了页内桌宠状态联动，让模型回复不仅是文本，还能驱动前端状态变化。
8. 后续我计划升级向量 RAG、长期记忆抽取和真实工具调用。

这个讲法的重点是：你不是只做了一个聊天页面，而是在学习并实现 Agent 工程的核心组成部分。

## 13. 一句话总结

这个项目目前已经完成了一个 Agent 原型的主干：前端交互、后端接口、模型调用、人设提示词、RAG、历史记忆、多 Agent 路由、Skills/MCP 扩展框架和页内桌宠联动。接下来最值得继续做的，不是盲目加大功能，而是把每一段链路吃透，并逐步把“预留框架”升级成“真实可执行能力”。

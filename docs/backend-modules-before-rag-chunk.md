# 后端模块整理说明：RAG Chunk 前置阶段

本次整理的目标是把原来集中在 `main.py` 里的后端逻辑拆开，让后续升级 RAG 的 `chunk -> embedding -> vector db` 时，只需要主要改 `services/rag_service.py`，不必反复碰接口层和聊天主流程。

## 当前模块结构

```text
main.py
core/
  settings.py
  file_store.py
  llm_client.py
schemas/
  chat.py
services/
  chat_service.py
  rag_service.py
  memory_service.py
  runtime_service.py
  agent_router.py
  pet_service.py
  keyword_service.py
```

## 每个模块负责什么

### `main.py`

只负责 FastAPI 接口：

- `GET /health`
- `GET /runtime/config`
- `GET /history/{session_id}`
- `POST /chat`

它不再直接处理 RAG、记忆、模型调用和路由。

### `core/settings.py`

集中保存全局配置：

- 项目路径
- knowledge / memory / config 路径
- DeepSeek 模型名
- 历史消息数量
- 摘要刷新规则
- 默认系统提示词
- 会话摘要提示词

后续如果要改模型名、RAG 路径、记忆路径，优先看这里。

### `core/file_store.py`

集中保存文件读写工具：

- 读取 Markdown 知识库
- 读取 JSON
- 写入 JSON
- 读取 JSONL
- 解析配置文件相对路径

后续做 chunk 时，可以继续复用这里的文件读取逻辑。

### `core/llm_client.py`

集中创建 OpenAI 兼容客户端：

```python
client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)
```

当前聊天和会话摘要都共用这个 client。

### `schemas/chat.py`

保存接口请求结构：

```python
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
```

后续如果前端要传更多字段，比如 `user_id`、`temperature`、`active_agent`，应该先在这里扩展。

### `services/chat_service.py`

聊天主编排服务，是后端 Agent 的主流程。

它负责：

1. 确认 `session_id`
2. 加载运行时配置
3. 路由到主 Agent 或专项 Agent
4. 构建模型 messages
5. 注入 RAG context
6. 注入会话摘要
7. 注入历史消息
8. 调用 DeepSeek
9. 保存用户消息和助手消息
10. 更新会话摘要
11. 生成桌宠状态
12. 返回前端需要的 JSON

后续只要 `/chat` 逻辑不变，前端 Web、桌面客户端、exe 都可以继续复用它。

### `services/rag_service.py`

当前仍然是轻量关键词 RAG。

它负责：

- 从 `knowledge/persona/` 读取人设资料
- 从 `knowledge/world/` 读取世界观资料
- 从 `memory/user_profile.json` 和 `memory/memories.jsonl` 读取长期记忆
- 用关键词评分选出相关内容
- 拼成 `rag_context`

下一步做 chunk 时，应该主要改这个文件。

### `services/memory_service.py`

负责记忆相关能力：

- 初始化 memory 文件
- 保存聊天历史
- 读取聊天历史
- 生成最近历史 messages
- 读取 / 保存会话摘要
- 自动判断是否刷新摘要
- 构建记忆追问上下文

它解决的是“Agent 如何记住当前会话和长期信息”的问题。

### `services/runtime_service.py`

负责读取配置：

- Agent 注册表
- Skills 注册表
- MCP 注册表
- Agent 系统提示词
- 前端运行时配置

前端的 Agent / Skills / MCP 面板主要依赖这个模块返回的数据。

### `services/agent_router.py`

负责判断当前消息应该由哪个 Agent 处理。

当前是关键词路由：

- 音乐相关 -> `music-agent`
- 图像相关 -> `image-agent`
- 桌宠相关 -> `pet-agent`
- 普通聊天 -> `utasama-main`

后续可以升级为模型意图识别，但初学阶段关键词路由更好理解。

### `services/pet_service.py`

负责根据用户消息、模型回复和路由结果生成桌宠状态。

返回结构：

```json
{
  "mood": "sunny",
  "animationState": "idle",
  "voiceLine": "...",
  "gesture": "...",
  "followUpHint": "..."
}
```

前端根据 `animationState` 切换桌宠图片和动画。

### `services/keyword_service.py`

集中保存关键词和简单文本评分函数。

当前用于：

- Agent 路由
- RAG 检索
- 情绪判断
- 记忆追问识别
- 桌宠状态判断

后续升级向量 RAG 时，这个文件仍然可以保留，用来做规则补充和意图判断。

## 当前数据流

```text
frontend/app.js
  ↓ POST /chat
main.py
  ↓
services/chat_service.py
  ↓
agent_router 检测 Agent
rag_service 检索知识库
memory_service 读取历史和摘要
runtime_service 读取人设和 Agent 配置
  ↓
DeepSeek
  ↓
memory_service 保存历史
pet_service 生成桌宠状态
  ↓
main.py 返回 JSON
  ↓
frontend/app.js 渲染页面
```

## 下一步做 RAG Chunk 时从哪里开始

下一阶段不要先改 `/chat`，先单独改 RAG。

建议新增：

```text
knowledge/raw/
knowledge/chunks/
```

然后在 `services/rag_service.py` 里逐步增加：

```python
load_raw_documents()
split_text_into_chunks()
build_chunk_records()
save_chunks()
load_chunks()
```

下一阶段先只做 chunk，不做 embedding。

也就是说，下一阶段目标是：

```text
Markdown 原文
  ↓
按标题 / 段落 / 字数切块
  ↓
生成 chunks.jsonl
  ↓
仍然用关键词在 chunks 中检索
```

等 chunk 跑通后，再进入：

```text
chunk -> embedding -> ChromaDB -> 向量检索
```

这样学习曲线最平滑。

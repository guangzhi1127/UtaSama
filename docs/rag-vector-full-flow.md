# UtaSama RAG 向量库全流程学习笔记

这份文档记录当前项目从“关键词 RAG”升级到“chunk + embedding + ChromaDB 向量检索”的完整流程。它面向初学者，重点不是堆概念，而是让你知道每一步在项目里对应哪个文件、怎么运行、怎么验收。

## 1. 先理解一句话

RAG 的核心流程是：

```text
知识文档
  -> 切成 chunk
  -> 用 embedding 模型转成向量
  -> 存进向量数据库
  -> 用户提问也转成向量
  -> 找最相似的 chunk
  -> 把 chunk 拼进大模型上下文
  -> 大模型依据资料回答
```

大模型不会自动读取你的本地文件，也不会自动上网查资料。RAG 是我们在工程代码里主动完成“查资料并塞给模型”的过程。

## 2. 当前使用的技术栈

```text
FastAPI                 后端接口
DeepSeek                聊天生成模型
sentence-transformers   本地 embedding 模型加载与向量生成
BAAI/bge-small-zh-v1.5  中文 embedding 模型
ChromaDB                本地向量数据库
JSONL                   保存 chunk 中间结果
Markdown                保存人设和世界观知识库
```

依赖写在根目录：

```text
requirements.txt
```

新增依赖：

```text
chromadb
sentence-transformers
```

## 3. 当前 RAG 文件结构

```text
knowledge/
  persona/
    00_core.md
    01_voice.md
    02_boundaries.md
  world/
    00_setting.md
    01_relationships.md
  chunks/
    chunks.jsonl
  vector_db/
    chroma/
```

说明：

- `knowledge/persona/`：角色人设资料。
- `knowledge/world/`：世界观、人物关系、能力设定资料。
- `knowledge/chunks/chunks.jsonl`：由 Markdown 自动切出来的 chunk。
- `knowledge/vector_db/chroma/`：ChromaDB 本地向量库，已加入 `.gitignore`，不建议提交到 GitHub。

## 4. 当前新增和修改的核心文件

### `services/rag_service.py`

这是 RAG 的核心服务，现在负责：

- 读取知识库 Markdown。
- 按标题、段落、字数切 chunk。
- 保存 `chunks.jsonl`。
- 加载 embedding 模型。
- 生成文本向量。
- 重建 ChromaDB 向量索引。
- 查询向量库。
- 向聊天主流程返回 RAG context。
- 如果向量依赖缺失或向量库为空，自动降级到旧关键词检索。

### `services/chat_service.py`

聊天主流程现在调用：

```python
build_rag_payload(payload.message)
```

它会返回：

```python
{
    "context": "...",
    "mode": "vector",
    "matches": [...],
    "error": ""
}
```

其中：

- `context`：最终拼进模型上下文的资料。
- `mode`：当前使用 `vector` 还是 `keyword-fallback`。
- `matches`：向量库命中的 chunk。
- `error`：降级原因或错误信息。

### `main.py`

新增 RAG 调试接口：

```text
GET  /rag/status
POST /rag/chunks/rebuild
POST /rag/vector/rebuild
GET  /rag/search
```

这些接口可以在：

```text
http://127.0.0.1:8000/docs
```

直接测试。

### `scripts/`

新增命令行脚本：

```text
scripts/rebuild_rag_chunks.py
scripts/rebuild_rag_vector.py
scripts/search_rag.py
```

它们适合你学习和调试 RAG 时单独运行。

## 5. Chunk 是什么

chunk 可以理解成“知识卡片”。

不要把一整篇文档都丢给向量库，因为：

- 文档太长时，检索不精确。
- 用户只问一个细节时，不需要整篇都返回。
- 大模型上下文有限，塞太多资料会干扰回答。

所以我们先把 Markdown 切成较短片段。当前配置在：

```text
core/settings.py
```

关键参数：

```python
RAG_CHUNK_SIZE = 420
RAG_CHUNK_OVERLAP = 80
```

意思是：

- 每个 chunk 目标长度约 420 个字符。
- 相邻 chunk 可以重叠约 80 个字符，避免一句话被切断后上下文丢失。

当前知识库比较短，所以 5 篇 Markdown 生成了 5 个 chunk。等你补充长文档后，chunk 数量会自然增加。

## 6. Embedding 是什么

embedding 是“把文本变成数字向量”。

例如：

```text
乌塔和路飞是什么关系
```

会被模型转成类似：

```text
[0.031, -0.125, 0.442, ...]
```

知识库里的每个 chunk 也会被转成向量。这样我们就可以比较：

```text
用户问题向量 和 每个 chunk 向量 谁更接近
```

越接近，说明语义越相关。

当前使用的 embedding 模型是：

```python
BAAI/bge-small-zh-v1.5
```

它适合中文语义检索，体积相对可控，适合当前项目入门阶段。

## 7. ChromaDB 是什么

ChromaDB 是本地向量数据库。

它负责保存：

- chunk 文本
- chunk metadata
- chunk embedding 向量

查询时它负责返回最相似的 chunk。

当前向量库目录：

```text
knowledge/vector_db/chroma/
```

这个目录是机器生成的，本地能用就行，不建议上传 GitHub。

## 8. 如何运行完整 RAG 流程

### 第一步：安装依赖

确保已经激活虚拟环境：

```powershell
.\.venv\Scripts\Activate.ps1
```

如果 PowerShell 禁止激活：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

安装依赖：

```powershell
python -m pip install -r requirements.txt
```

### 第二步：重建 chunks

```powershell
python scripts/rebuild_rag_chunks.py
```

成功时会看到类似：

```json
{
  "status": "ok",
  "chunk_count": 5
}
```

### 第三步：重建向量库

```powershell
python scripts/rebuild_rag_vector.py
```

第一次运行会下载 embedding 模型，可能稍慢。

成功时会看到：

```json
{
  "status": "ok",
  "collection": "utasama_knowledge",
  "indexed_count": 5
}
```

### 第四步：搜索测试

```powershell
python scripts/search_rag.py 乌塔和路飞是什么关系
```

预期第一条应该命中：

```text
world/01_relationships.md
```

这说明向量库不是机械匹配字面关键词，而是在找语义相关内容。

## 9. 如何通过网页接口测试

启动后端：

```powershell
fastapi dev main.py
```

打开：

```text
http://127.0.0.1:8000/docs
```

可以测试：

```text
GET /rag/status
```

看依赖、chunk 数量、向量库数量。

可以测试：

```text
POST /rag/chunks/rebuild
```

只重建 chunk。

可以测试：

```text
POST /rag/vector/rebuild
```

重建 chunk 并写入向量库。

可以测试：

```text
GET /rag/search?query=乌塔和香克斯是什么关系
```

查看向量库命中的 chunk。

## 10. 聊天时 RAG 如何生效

聊天流程现在是：

```text
用户输入
  -> chat_service.py
  -> build_rag_payload()
  -> ChromaDB 检索相关 chunk
  -> 拼成 [向量知识库检索结果]
  -> 放入 DeepSeek messages
  -> DeepSeek 依据资料回答
```

后端 `/chat` 返回里新增了：

```json
{
  "rag_mode": "vector",
  "rag_match_count": 5,
  "rag_error": "",
  "rag_preview": "..."
}
```

你可以通过前端调试信息或接口返回判断当前是否用了向量检索。

## 11. 如何新增知识库资料

以后你想补设定，不要改代码，优先新增 Markdown。

例如：

```text
knowledge/world/02_uta_ability.md
knowledge/world/03_movie_events.md
knowledge/persona/03_emotion_style.md
```

建议格式：

```markdown
# 标题

## 小节一

- 事实点 1
- 事实点 2
- 回答边界

## 小节二

这里写更具体的说明。
```

新增或修改 Markdown 后，必须重新执行：

```powershell
python scripts/rebuild_rag_vector.py
```

因为向量库不会自动知道文件变了，需要重新切 chunk、重新 embedding、重新写入 ChromaDB。

## 12. 当前阶段到哪里为止

目前已经做到：

- 文档读取
- chunk 切块
- chunks.jsonl 保存
- embedding 模型接入
- ChromaDB 本地向量库
- 向量检索
- 聊天主流程接入 RAG payload
- 关键词检索降级
- RAG 调试接口
- RAG 命令行脚本

这已经是一个完整的入门级 RAG 系统。

下一阶段可以继续做：

- 前端增加 RAG 调试面板。
- 长期记忆也向量化。
- 文档变更自动检测。
- RAG 命中阈值和 rerank。
- 把网页 UI 封装到本地客户端。

但在封装客户端之前，当前最重要的是先吃透：

```text
chunk -> embedding -> vector db -> retrieve -> prompt injection
```

这就是 RAG 的主干。

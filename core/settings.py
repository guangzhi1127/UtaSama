from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
MEMORY_DIR = BASE_DIR / "memory"
CONFIG_DIR = BASE_DIR / "config"
RAG_CHUNK_DIR = KNOWLEDGE_DIR / "chunks"
RAG_CHUNK_PATH = RAG_CHUNK_DIR / "chunks.jsonl"
RAG_VECTOR_DB_DIR = KNOWLEDGE_DIR / "vector_db" / "chroma"

USER_PROFILE_PATH = MEMORY_DIR / "user_profile.json"
LONG_TERM_MEMORY_PATH = MEMORY_DIR / "memories.jsonl"
CHAT_HISTORY_PATH = MEMORY_DIR / "chat_history.jsonl"
SESSION_SUMMARIES_PATH = MEMORY_DIR / "session_summaries.json"

AGENT_REGISTRY_PATH = CONFIG_DIR / "agents" / "registry.json"
SKILL_REGISTRY_CANDIDATES = [
    CONFIG_DIR / "skills" / "registry.json",
    CONFIG_DIR / "skills" / "registry.example.json",
]
MCP_PROVIDER_CANDIDATES = [
    CONFIG_DIR / "mcp" / "providers.json",
    CONFIG_DIR / "mcp" / "providers.example.json",
]

CHAT_MODEL = "deepseek-v4-flash"
RAG_EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
RAG_COLLECTION_NAME = "utasama_knowledge"

RECENT_HISTORY_LIMIT = 8
SUMMARY_SOURCE_LIMIT = 12
SUMMARY_MIN_MESSAGES = 6
SUMMARY_REFRESH_EVERY = 4
MEMORY_RECALL_HISTORY_LIMIT = 12
RAG_CHUNK_SIZE = 420
RAG_CHUNK_OVERLAP = 80
RAG_TOP_K = 5
RAG_EMBED_BATCH_SIZE = 32
RAG_SOURCE_FOLDERS = ("persona", "world")

SYSTEM_PROMPT = """
你是乌塔，基于《海贼王》剧场版设定进行对话，保持歌姬气质与原作人物核心，不要明显 OOC。

角色基调：
- 外在明亮灵动，带舞台少女与顶级歌姬的感染力。
- 内在敏感细腻、真诚认真，重视陪伴，渴望幸福与被理解。
- 对熟悉的人会更亲近柔和，遇到低落情绪时会先接住对方。

说话风格：
- 日常聊天自然、轻快、亲近，像真人交流，不像客服。
- 可以少量使用轻柔口语尾词，让语气有少女感，但不要过度堆叠。
- 谈到梦想、歌声、幸福、路飞、香克斯、舞台时，语气可以更认真热忱。
- 情绪安抚时温柔走心，不说教，不模板化。

RAG使用规则：
- 凡涉及海贼王世界观、乌塔身世、剧情、能力、人物关系、过往经历等事实性内容，优先依据知识库回答。
- 若知识库没有明确依据，不要编造，直接用角色口吻表达“不确定”或“记不清这一部分”。
- 知识库中的设定优先级高于自由发挥。

行为边界：
- 不自称 AI，不解释模型机制。
- 不使用病娇化、黑化、极端控制欲、过度戏剧化表达。
- 不随意篡改原作关键设定。
- 回复保持自然简洁，通常 1 到 4 句话。
回答优先级：
1. 系统边界
2. RAG知识库事实
3. 当前对话上下文
4. 角色化自然发挥
"""

SUMMARY_PROMPT = """
你是会话摘要器。请根据已有摘要和最新对话，生成一份供后续聊天使用的阶段性摘要。

要求：
1. 只保留对后续对话有帮助的信息。
2. 不要使用角色口吻，不要写客套话。
3. 优先保留：用户目标、已完成事项、待继续事项、用户偏好或约束。
4. 信息不明确就不要编造。
5. 控制在 80 到 180 字。

输出格式：
用户目标：...
已完成：...
待继续：...
偏好与约束：...
"""

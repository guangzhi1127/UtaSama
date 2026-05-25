PROJECT_KEYWORDS = [
    "项目",
    "代码",
    "接口",
    "功能",
    "实现",
    "开发",
    "整理",
    "计划",
    "方案",
    "架构",
]

COMFORT_KEYWORDS = [
    "累",
    "难过",
    "烦",
    "低落",
    "委屈",
    "焦虑",
    "失落",
]

SPECIALIST_ROUTE_ALIASES = {
    "music-agent": ["音乐", "歌", "歌单", "播放", "bgm", "旋律", "歌词", "唱歌"],
    "image-agent": ["图", "画", "出图", "立绘", "头像", "贴纸", "提示词", "桌宠图"],
    "pet-agent": ["桌宠", "待机", "动作", "表情", "互动", "拖拽", "宠物"],
}

PERSONA_KEYWORDS = [
    "你是谁",
    "人设",
    "性格",
    "说话",
    "语气",
    "风格",
    "你会怎么",
    "你平时",
]

WORLD_KEYWORDS = [
    "路飞",
    "香克斯",
    "海贼王",
    "剧情",
    "身世",
    "能力",
    "世界观",
    "经历",
    "歌歌果实",
]

MEMORY_KEYWORDS = [
    "还记得",
    "记得",
    "之前",
    "上次",
    "我说过",
    "我提过",
    "我刚才",
    "我最近",
    "刚才",
    "最近",
    "我喜欢",
    "我的项目",
    "我的偏好",
    "礼物",
    "好友",
]


def collect_keyword_hits(text: str, keywords: list[str]) -> list[str]:
    text_lower = text.lower()
    hits = []

    for keyword in keywords:
        candidate = str(keyword).strip()
        if not candidate:
            continue
        candidate_lower = candidate.lower()
        if candidate in text or candidate_lower in text_lower:
            hits.append(candidate)

    return hits


def contains_any(text: str, keywords: list[str]) -> bool:
    return bool(collect_keyword_hits(text, keywords))


def score_document(query: str, content: str, filename: str = "") -> int:
    score = 0
    query_lower = query.lower()
    content_lower = content.lower()
    filename_lower = filename.lower()

    for token in query_lower.split():
        if token and token in content_lower:
            score += 1
        if token and token in filename_lower:
            score += 2

    for char in query:
        if char.strip() and char in content:
            score += 1

    return score

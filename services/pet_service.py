from services.keyword_service import COMFORT_KEYWORDS, contains_any


def build_pet_state(user_message: str, reply_text: str, route: dict) -> dict:
    text = f"{user_message} {reply_text}"
    active_agent = str(route.get("active_agent", "utasama-main")).strip()
    intent = str(route.get("intent", "companion-chat")).strip()

    def make_state(
        mood: str,
        animation_state: str,
        voice_line: str,
        gesture: str,
        follow_up_hint: str,
    ) -> dict:
        return {
            "mood": mood,
            "animationState": animation_state,
            "voiceLine": voice_line,
            "gesture": gesture,
            "followUpHint": follow_up_hint,
        }

    if contains_any(text, COMFORT_KEYWORDS):
        return make_state(
            mood="gentle",
            animation_state="idle",
            voice_line="我在，先慢一点也没关系。",
            gesture="soft-wave",
            follow_up_hint="要是你想慢慢说，我就继续陪着你。",
        )

    if active_agent == "music-agent" or contains_any(
        text, ["唱歌", "音乐", "歌单", "旋律", "舞台", "BGM", "bgm"]
    ):
        return make_state(
            mood="idol",
            animation_state="sing",
            voice_line="这句有舞台感，我已经跟着节奏摇起来了。",
            gesture="note-sway",
            follow_up_hint="你继续说歌或者情绪，我能陪你往下接。",
        )

    if active_agent == "image-agent" or contains_any(
        text, ["图", "立绘", "出图", "头像", "贴纸", "提示词", "桌宠图"]
    ):
        return make_state(
            mood="serious",
            animation_state="think",
            voice_line="收到，我先帮你把规格和画面想清楚。",
            gesture="thinking-tilt",
            follow_up_hint="你要是继续补风格和用途，我会更快进入状态。",
        )

    if active_agent == "pet-agent" or contains_any(
        text, ["提醒", "注意", "等下", "马上", "快点", "盯着"]
    ):
        return make_state(
            mood="protective",
            animation_state="alert",
            voice_line="我盯着呢，有动静我会先提醒你。",
            gesture="alert-burst",
            follow_up_hint="这段先交给我盯着，你继续忙也行。",
        )

    if contains_any(text, ["完成", "好耶", "太好了", "谢谢", "开心", "顺利"]):
        return make_state(
            mood="sunny",
            animation_state="happy",
            voice_line="好耶，这种时候就该让我开心一下。",
            gesture="sparkle-hop",
            follow_up_hint="如果你要继续推进，我也能立刻跟上。",
        )

    if intent in {"memory-recall", "project-support"} or contains_any(
        text, ["任务", "安排", "计划", "效率", "整理", "还记得"]
    ):
        return make_state(
            mood="serious",
            animation_state="think",
            voice_line="收到，我先帮你把节奏稳住。",
            gesture="thinking-tilt",
            follow_up_hint="你继续抛给我，我会帮你把线索拎出来。",
        )

    return make_state(
        mood="sunny",
        animation_state="idle",
        voice_line="我在旁边听着，状态正常。",
        gesture="idle-sway",
        follow_up_hint="点我一下也行，我会继续陪你待机。",
    )

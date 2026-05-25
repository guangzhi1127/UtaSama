from __future__ import annotations

from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from PySide6.QtCore import QEvent, Qt, QThreadPool, QTimer
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from desktop.api_client import ApiResult, UtaSamaApiClient
from desktop.ui.styles import APP_STYLE, ASSISTANT_BUBBLE_STYLE, SYSTEM_BUBBLE_STYLE, USER_BUBBLE_STYLE
from desktop.worker import ApiWorker


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_ASSET_DIR = PROJECT_ROOT / "frontend" / "assets"
DESKTOP_ASSET_DIR = PROJECT_ROOT / "desktop" / "assets"
AVATAR_PATH = FRONTEND_ASSET_DIR / "uta-avatar.jpg"
PET_STATE_DIR = FRONTEND_ASSET_DIR / "pet-states"
WALLPAPER_PATH = DESKTOP_ASSET_DIR / "wallpaper-placeholder.png"
LEFT_HEADPHONE_PATH = DESKTOP_ASSET_DIR / "headphone-left.png"
RIGHT_HEADPHONE_PATH = DESKTOP_ASSET_DIR / "headphone-right.png"


class WallpaperFrame(QFrame):
    def __init__(self, wallpaper_path: Path, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.wallpaper_path = wallpaper_path
        self.wallpaper = QPixmap(str(wallpaper_path)) if wallpaper_path.exists() else QPixmap()
        self.setObjectName("ChatWallpaper")

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if not self.wallpaper.isNull():
            scaled = self.wallpaper.scaled(
                self.size(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation,
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
            painter.fillRect(self.rect(), QColor(255, 250, 250, 174))
        else:
            gradient = QLinearGradient(0, 0, self.width(), self.height())
            gradient.setColorAt(0, QColor("#fff2f5"))
            gradient.setColorAt(0.45, QColor("#fffaf6"))
            gradient.setColorAt(1, QColor("#f8f5f1"))
            painter.fillRect(self.rect(), gradient)
            painter.fillRect(self.rect(), QColor(255, 255, 255, 80))

        painter.end()
        super().paintEvent(event)


class ChatBubble(QFrame):
    def __init__(self, role: str, text: str, meta: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(10, 6, 10, 6)
        outer.setSpacing(8)

        if role == "system":
            outer.addStretch(1)
            bubble = QLabel(text)
            bubble.setWordWrap(True)
            bubble.setTextInteractionFlags(Qt.TextSelectableByMouse)
            bubble.setMaximumWidth(560)
            bubble.setAlignment(Qt.AlignCenter)
            bubble.setStyleSheet(SYSTEM_BUBBLE_STYLE)
            outer.addWidget(bubble)
            outer.addStretch(1)
            return

        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setTextInteractionFlags(Qt.TextSelectableByMouse)
        bubble.setMaximumWidth(540)
        bubble.setMinimumWidth(80)

        if role == "user":
            bubble.setStyleSheet(USER_BUBBLE_STYLE)
            outer.addStretch(1)
            outer.addWidget(bubble)
            outer.addWidget(self._build_user_avatar())
            return

        bubble.setStyleSheet(ASSISTANT_BUBBLE_STYLE)
        outer.addWidget(self._build_assistant_avatar())
        wrapper = QVBoxLayout()
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.setSpacing(3)
        if meta:
            meta_label = QLabel(meta)
            meta_label.setObjectName("Subtitle")
            wrapper.addWidget(meta_label)
        wrapper.addWidget(bubble)
        holder = QWidget()
        holder.setLayout(wrapper)
        outer.addWidget(holder)
        outer.addStretch(1)

    @staticmethod
    def _build_assistant_avatar() -> QLabel:
        avatar = QLabel()
        avatar.setFixedSize(38, 38)
        avatar.setAlignment(Qt.AlignCenter)
        if AVATAR_PATH.exists():
            avatar.setPixmap(
                QPixmap(str(AVATAR_PATH)).scaled(
                    38,
                    38,
                    Qt.KeepAspectRatioByExpanding,
                    Qt.SmoothTransformation,
                )
            )
        avatar.setStyleSheet("background: #fff; border: 1px solid #d9ac52; border-radius: 8px;")
        return avatar

    @staticmethod
    def _build_user_avatar() -> QLabel:
        avatar = QLabel("你")
        avatar.setFixedSize(38, 38)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(
            "background: #2f3640; color: #fff; border-radius: 8px; font-weight: 700;"
        )
        return avatar


class MainWindow(QMainWindow):
    def __init__(self, api_base_url: str = "http://127.0.0.1:8000"):
        super().__init__()
        self.api_client = UtaSamaApiClient(api_base_url)
        self.thread_pool = QThreadPool.globalInstance()
        self.session_id = f"desktop_{uuid4().hex[:12]}"
        self.is_waiting = False
        self.runtime_config: dict[str, Any] = {}

        self.setWindowTitle("UtaSama Desktop")
        self.resize(1240, 780)
        self.setMinimumSize(1040, 660)
        self.setStyleSheet(APP_STYLE)

        self._build_ui()
        self._connect_events()
        self.add_message("assistant", "桌面客户端已经启动啦。现在像聊天框一样直接和我说话就好。", "UtaSama")
        self.run_api_task("health")
        self.run_api_task("runtime")

    def _build_ui(self) -> None:
        self.root = QFrame()
        self.root.setObjectName("RootFrame")
        root_layout = QVBoxLayout(self.root)
        root_layout.setContentsMargins(16, 14, 16, 14)
        root_layout.setSpacing(12)

        root_layout.addWidget(self._build_top_bar(), 0)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(12)
        body.addWidget(self._build_conversation_panel(), 0)
        body.addWidget(self._build_chat_panel(), 1)
        body.addWidget(self._build_right_panel(), 0)
        root_layout.addLayout(body, 1)

        self._build_headphone_decorations()
        self.setCentralWidget(self.root)

    def _build_top_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("TopBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 9, 14, 9)
        layout.setSpacing(10)

        title = QLabel("UtaSama")
        title.setObjectName("Title")
        subtitle = QLabel("微信式本地 Agent 聊天客户端")
        subtitle.setObjectName("Subtitle")

        title_box = QVBoxLayout()
        title_box.setContentsMargins(0, 0, 0, 0)
        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        self.backend_status = QLabel("后端：检测中")
        self.backend_status.setObjectName("StatusPill")
        self.agent_label = QLabel("Agent：等待配置")
        self.agent_label.setObjectName("StatusPill")
        self.route_label = QLabel("路由：待机")
        self.route_label.setObjectName("StatusPill")

        self.reload_button = QPushButton("刷新配置")
        self.health_button = QPushButton("检查后端")

        layout.addLayout(title_box)
        layout.addStretch(1)
        layout.addWidget(self.backend_status)
        layout.addWidget(self.agent_label)
        layout.addWidget(self.route_label)
        layout.addWidget(self.reload_button)
        layout.addWidget(self.health_button)
        return bar

    def _build_conversation_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("ConversationPanel")
        panel.setFixedWidth(248)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        header = QLabel("会话")
        header.setObjectName("SectionTitle")
        search = QLabel("搜索 / 新建会话（预留）")
        search.setObjectName("SearchBox")

        layout.addWidget(header)
        layout.addWidget(search)
        layout.addWidget(self._build_conversation_item("UtaSama", "当前聊天主 Agent", True))
        layout.addWidget(self._build_conversation_item("桌宠状态", "pet_state 实时联动", False))
        layout.addWidget(self._build_conversation_item("RAG 知识库", "向量检索结果预览", False))
        layout.addStretch(1)

        self.session_label = QLabel(f"会话：{self.session_id}")
        self.session_label.setObjectName("StatusPill")
        layout.addWidget(self.session_label)
        return panel

    def _build_conversation_item(self, title: str, subtitle: str, active: bool) -> QWidget:
        item = QFrame()
        item.setObjectName("ConversationItemActive" if active else "ConversationItem")
        layout = QHBoxLayout(item)
        layout.setContentsMargins(9, 8, 9, 8)
        layout.setSpacing(9)

        avatar = QLabel(title[:1])
        avatar.setFixedSize(34, 34)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(
            "background: #d83a45; color: #fff; border-radius: 8px; font-weight: 700;"
            if active
            else "background: #f8f1ea; color: #8a6751; border: 1px solid #e3c991; border-radius: 8px;"
        )

        text_box = QVBoxLayout()
        text_box.setContentsMargins(0, 0, 0, 0)
        title_label = QLabel(title)
        title_label.setObjectName("SectionTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("Subtitle")
        subtitle_label.setWordWrap(True)
        text_box.addWidget(title_label)
        text_box.addWidget(subtitle_label)

        layout.addWidget(avatar)
        layout.addLayout(text_box, 1)
        return item

    def _build_chat_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("ChatPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        chat_header = QHBoxLayout()
        title = QLabel("UtaSama")
        title.setObjectName("SectionTitle")
        hint = QLabel("背景壁纸位：desktop/assets/wallpaper-placeholder.png")
        hint.setObjectName("Subtitle")
        chat_header.addWidget(title)
        chat_header.addStretch(1)
        chat_header.addWidget(hint)

        self.wallpaper_frame = WallpaperFrame(WALLPAPER_PATH)
        wallpaper_layout = QVBoxLayout(self.wallpaper_frame)
        wallpaper_layout.setContentsMargins(10, 10, 10, 10)
        wallpaper_layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("background: transparent;")
        self.message_container = QWidget()
        self.message_container.setStyleSheet("background: transparent;")
        self.message_layout = QVBoxLayout(self.message_container)
        self.message_layout.setContentsMargins(0, 0, 0, 0)
        self.message_layout.setSpacing(2)
        self.message_layout.addStretch(1)
        self.scroll_area.setWidget(self.message_container)
        wallpaper_layout.addWidget(self.scroll_area, 1)

        input_row = QHBoxLayout()
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("输入消息，按 Ctrl+Enter 发送")
        self.message_input.setFixedHeight(82)
        self.message_input.installEventFilter(self)
        self.send_button = QPushButton("发送")
        self.send_button.setFixedWidth(92)
        input_row.addWidget(self.message_input, 1)
        input_row.addWidget(self.send_button)

        layout.addLayout(chat_header)
        layout.addWidget(self.wallpaper_frame, 1)
        layout.addLayout(input_row)
        return panel

    def _build_right_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("RightPanel")
        panel.setFixedWidth(282)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        title = QLabel("状态面板")
        title.setObjectName("SectionTitle")

        self.pet_image = QLabel()
        self.pet_image.setFixedSize(164, 164)
        self.pet_image.setAlignment(Qt.AlignCenter)
        self.pet_image.setStyleSheet("background: #fff; border: 1px solid #ead3c3; border-radius: 8px;")

        self.pet_status = QLabel("桌宠：待机 / sunny")
        self.pet_status.setObjectName("GoldPill")
        self.pet_line = QLabel("我在这里待机，等你发消息。")
        self.pet_line.setWordWrap(True)
        self.pet_line.setObjectName("StatusPill")

        self.rag_status = QLabel("RAG：未检索")
        self.rag_status.setObjectName("StatusPill")
        self.rag_detail = QLabel("命中：0\n错误：无")
        self.rag_detail.setWordWrap(True)
        self.rag_detail.setObjectName("StatusPill")

        self.intent_status = QLabel("意图：等待消息")
        self.intent_status.setWordWrap(True)
        self.intent_status.setObjectName("StatusPill")
        self.skill_status = QLabel("Skills：暂无\nMCP：暂无")
        self.skill_status.setWordWrap(True)
        self.skill_status.setObjectName("StatusPill")

        layout.addWidget(title)
        layout.addWidget(self.pet_image, 0, Qt.AlignHCenter)
        layout.addWidget(self.pet_status)
        layout.addWidget(self.pet_line)
        layout.addSpacing(8)
        layout.addWidget(self.rag_status)
        layout.addWidget(self.rag_detail)
        layout.addWidget(self.intent_status)
        layout.addWidget(self.skill_status)
        layout.addStretch(1)

        self.update_pet_image("idle")
        return panel

    def _build_headphone_decorations(self) -> None:
        self.left_headphone = QLabel(self.root)
        self.right_headphone = QLabel(self.root)
        for label, path in (
            (self.left_headphone, LEFT_HEADPHONE_PATH),
            (self.right_headphone, RIGHT_HEADPHONE_PATH),
        ):
            label.setFixedSize(132, 132)
            label.setAttribute(Qt.WA_TransparentForMouseEvents)
            label.setStyleSheet("background: transparent;")
            if path.exists():
                label.setPixmap(
                    QPixmap(str(path)).scaled(
                        132,
                        132,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )
                )
            label.raise_()

    def _connect_events(self) -> None:
        self.send_button.clicked.connect(self.submit_message)
        self.reload_button.clicked.connect(lambda: self.run_api_task("runtime"))
        self.health_button.clicked.connect(lambda: self.run_api_task("health"))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "left_headphone"):
            self.left_headphone.move(14, 48)
            self.right_headphone.move(max(14, self.root.width() - 146), 48)

    def run_api_task(self, task: str, message: str = "") -> None:
        worker = ApiWorker(task, self.api_client, message=message, session_id=self.session_id)
        worker.signals.finished.connect(self.handle_api_result)
        self.thread_pool.start(worker)

    def submit_message(self) -> None:
        text = self.message_input.toPlainText().strip()
        if not text or self.is_waiting:
            return

        self.message_input.clear()
        self.add_message("user", text)
        self.set_waiting(True)
        self.add_message("system", "正在调用本地 FastAPI 后端和 RAG 向量库...")
        self.run_api_task("chat", message=text)

    def add_message(self, role: str, text: str, meta: str = "") -> None:
        bubble = ChatBubble(role, text, meta)
        self.message_layout.insertWidget(self.message_layout.count() - 1, bubble)
        QTimer.singleShot(0, self.scroll_to_bottom)

    def scroll_to_bottom(self) -> None:
        bar = self.scroll_area.verticalScrollBar()
        bar.setValue(bar.maximum())

    def set_waiting(self, waiting: bool) -> None:
        self.is_waiting = waiting
        self.send_button.setDisabled(waiting)
        self.send_button.setText("等待" if waiting else "发送")

    def handle_api_result(self, task: str, result: ApiResult) -> None:
        if task == "health":
            self.update_health(result)
            return

        if task == "runtime":
            self.update_runtime(result)
            return

        if task == "chat":
            self.set_waiting(False)
            if not result.ok:
                self.add_message("system", f"后端请求失败：{result.error}")
                self.backend_status.setText("后端：异常")
                return
            self.handle_chat_response(result.data)

    def update_health(self, result: ApiResult) -> None:
        if result.ok:
            self.backend_status.setText("后端：在线")
            self.backend_status.setStyleSheet("background: #eef8ee; border: 1px solid #9fcca2; border-radius: 8px; color: #35633c; padding: 6px 8px;")
        else:
            self.backend_status.setText("后端：未连接")
            self.backend_status.setStyleSheet("background: #fff0f0; border: 1px solid #dda5a5; border-radius: 8px; color: #8a3b3b; padding: 6px 8px;")
            self.add_message("system", "还没有连接到后端。请先运行：fastapi dev main.py")

    def update_runtime(self, result: ApiResult) -> None:
        if not result.ok:
            self.agent_label.setText("Agent：配置读取失败")
            return

        self.runtime_config = result.data
        entry_name = result.data.get("entry_agent_display_name") or result.data.get("entry_agent") or "utasama-main"
        skill_count = len(result.data.get("skills", []))
        mcp_count = len(result.data.get("mcp", []))
        self.agent_label.setText(f"Agent：{entry_name}")
        self.skill_status.setText(f"Skills：{skill_count} 项\nMCP：{mcp_count} 项")

    def handle_chat_response(self, data: dict[str, Any]) -> None:
        self.session_id = data.get("session_id") or self.session_id
        self.session_label.setText(f"会话：{self.session_id}")

        reply = data.get("reply_text") or "这次后端没有返回正文。"
        agent_name = data.get("agent_display_name") or "UtaSama"
        self.add_message("assistant", reply, agent_name)

        self.route_label.setText(f"路由：{agent_name}")
        self.intent_status.setText(
            "意图：{intent}\n原因：{reason}".format(
                intent=data.get("intent", "unknown"),
                reason=data.get("route_reason", "未返回"),
            )
        )
        self.rag_status.setText(
            "RAG：{mode} / {count}".format(
                mode=data.get("rag_mode", "unknown"),
                count=data.get("rag_match_count", 0),
            )
        )
        self.rag_detail.setText(
            "知识库：{used}\n错误：{error}".format(
                used="已使用" if data.get("rag_used") else "未使用",
                error=data.get("rag_error") or "无",
            )
        )
        self.skill_status.setText(
            "Skills：{skills}\nMCP：{mcp}".format(
                skills=self.format_list(data.get("preferred_skills")),
                mcp=self.format_list(data.get("preferred_mcp")),
            )
        )
        self.update_pet_state(data.get("pet_state") or {})

    def update_pet_state(self, pet_state: dict[str, Any]) -> None:
        mood = pet_state.get("mood", "sunny")
        animation_state = pet_state.get("animationState", "idle")
        voice_line = pet_state.get("voiceLine", "我在旁边听着。")
        self.pet_status.setText(f"桌宠：{animation_state} / {mood}")
        self.pet_line.setText(voice_line)
        self.update_pet_image(animation_state)

    def update_pet_image(self, animation_state: str) -> None:
        image_path = PET_STATE_DIR / f"{animation_state}.png"
        if not image_path.exists():
            image_path = PET_STATE_DIR / "idle.png"

        if image_path.exists():
            pixmap = QPixmap(str(image_path)).scaled(
                154,
                154,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.pet_image.setPixmap(pixmap)
        else:
            self.pet_image.setText("PET")

    @staticmethod
    def format_list(items: Any) -> str:
        if not isinstance(items, list) or not items:
            return "暂无"
        return " / ".join(str(item) for item in items)

    def keyPressEvent(self, event) -> None:
        if event.key() in {Qt.Key_Return, Qt.Key_Enter} and event.modifiers() & Qt.ControlModifier:
            self.submit_message()
            return
        super().keyPressEvent(event)

    def eventFilter(self, watched, event) -> bool:
        if watched is self.message_input and event.type() == QEvent.KeyPress:
            if event.key() in {Qt.Key_Return, Qt.Key_Enter} and event.modifiers() & Qt.ControlModifier:
                self.submit_message()
                return True
        return super().eventFilter(watched, event)

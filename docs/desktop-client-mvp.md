# UtaSama PySide6 桌面客户端 MVP

这是第一版桌面 UI 客户端。它不会替代现有网页前端，也不会改动后端 Agent 主链路，而是新增一个 Python 桌面窗口，通过 HTTP 调用当前 FastAPI 后端。

## 当前形态

```text
PySide6 桌面窗口
  -> requests
  -> http://127.0.0.1:8000/chat
  -> FastAPI 后端
  -> RAG / Memory / Agent / DeepSeek
```

这一版还不是 exe，但已经支持通过 `launcher.py` 一键启动本地后端和桌面客户端。

## 新增文件

```text
desktop/
  app.py
  api_client.py
  worker.py
  ui/
    main_window.py
    styles.py
```

职责说明：

- `launcher.py`：一键启动入口，负责启动后端、等待 `/health`、打开桌面客户端、关闭时收尾。
- `desktop/app.py`：桌面客户端启动入口。
- `desktop/api_client.py`：封装对 FastAPI 的 HTTP 请求。
- `desktop/worker.py`：后台线程执行请求，避免 UI 卡住。
- `desktop/ui/main_window.py`：主窗口、聊天区、桌宠区、RAG 状态区。
- `desktop/ui/styles.py`：桌面端样式。

## 运行方式

### 1. 激活虚拟环境

```powershell
.\.venv\Scripts\Activate.ps1
```

如果 PowerShell 禁止运行脚本：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 2. 安装依赖

```powershell
python -m pip install -r requirements.txt
```

### 3. 推荐：一键启动

在项目根目录运行：

```powershell
python launcher.py
```

它会自动完成：

```text
检测 http://127.0.0.1:8000/health
  -> 如果后端已在线，直接打开桌面客户端
  -> 如果后端未在线，启动 uvicorn main:app
  -> 等待 /health 返回 ok
  -> 打开 PySide6 桌面客户端
  -> 客户端关闭后，关闭由 launcher 启动的后端
```

启动器日志在：

```text
logs/launcher-backend.log
```

### 4. 可选：分开启动，适合调试

第一个终端运行：

```powershell
fastapi dev main.py
```

第二个终端运行：

```powershell
python -m desktop.app
```

如果后端端口不是默认的 `8000`，可以指定：

```powershell
python -m desktop.app --api-base-url http://127.0.0.1:8010
```

### 5. 启动器参数

```powershell
python launcher.py --host 127.0.0.1 --port 8000
```

常用参数：

```text
--port 8010      使用其他后端端口
--no-backend     不自动启动后端，只打开客户端并连接已有后端
--timeout 60     等待后端启动的最长秒数
--smoke          快速启动并自动退出，用于测试
```

默认后端地址：

```text
http://127.0.0.1:8000
```

## 当前 UI 结构

桌面端已经从仪表盘式布局调整为微信式聊天结构：

```text
顶部栏：
  UtaSama 标题 / 后端状态 / Agent 状态 / 当前路由

左侧：
  会话列表 / 搜索与新建会话预留 / 当前 session

中间：
  聊天主窗口 / 壁纸背景层 / 左右消息气泡 / 输入框

右侧：
  桌宠状态 / RAG 模式 / 意图 / Skills / MCP
```

视觉上保留乌塔发色与耳机意象：

- 整体左侧红色边框。
- 整体右侧白色边框。
- 上下金色细线。
- 两侧大号金色耳机装饰。
- 中间聊天区预留背景壁纸。

## 可替换素材

当前新增了 3 个桌面端占位素材：

```text
desktop/assets/wallpaper-placeholder.png
desktop/assets/headphone-left.png
desktop/assets/headphone-right.png
```

后续你只需要用同名 PNG 替换，就可以换成正式 UI 资产：

- `wallpaper-placeholder.png`：聊天区背景壁纸，建议 1400x900 或更大。
- `headphone-left.png`：左侧透明背景金色耳机。
- `headphone-right.png`：右侧透明背景金色耳机。

当前桌宠临时使用 GIF 动图：

```text
frontend/assets/pet-states/uta-live.gif
frontend/assets/pet-states/uta-live-alt.gif
```

Web 前端直接用 `<img>` 播放 GIF，桌面端用 `QMovie` 播放 GIF。后续可以逐步替换成多状态 GIF、Spine 或 Live2D。

## 当前 UI 功能

当前桌面端已经支持：

- 打开独立桌面窗口。
- 检查后端是否在线。
- 读取运行时 Agent / Skills / MCP 配置。
- 发送用户消息到 `/chat`。
- 显示用户消息和助手回复。
- 显示当前路由 Agent。
- 显示 RAG 模式和命中数量。
- 显示建议 Skills / MCP。
- 根据后端 `pet_state` 切换桌宠状态图。
- 支持 `Ctrl+Enter` 发送。
- 预留背景壁纸位置。
- 预留左右金色耳机装饰位。

## 验收方式

后端启动后，打开桌面客户端，测试：

```text
乌塔和路飞是什么关系
```

预期：

- 聊天区出现用户消息和助手回复。
- 右侧 RAG 显示 `vector / 5` 或类似结果。
- 当前路由显示主 Agent 或相关 Agent。
- 桌宠状态正常显示。

再测试：

```text
帮我整理桌宠出图提示词
```

预期：

- 路由可能命中图像相关 Agent。
- 桌宠状态可能切换为 `think`。
- 右侧 Skills / MCP 显示建议项。

## 下一阶段

桌面客户端下一阶段建议按这个顺序继续：

1. 替换正式壁纸和耳机装饰素材。
2. 增加设置页：API Key、模型名、后端地址。
3. 增加 RAG 检索来源展开面板。
4. 增加历史会话列表。
5. 让桌宠支持更多动作和半透明浮窗。
6. 自动启动 FastAPI 后端。
7. 用 PyInstaller 打包成 exe。

不要现在就直接打包 exe。先把桌面 UI 和后端联调稳定，再处理打包依赖、模型缓存、ChromaDB 路径和资源文件。

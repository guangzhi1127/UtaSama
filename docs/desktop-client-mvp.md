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

这一版还不是 exe，也不会自动启动后端。先分开运行，方便初学阶段调试。

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

### 3. 启动后端

在第一个终端运行：

```powershell
fastapi dev main.py
```

确认后端地址：

```text
http://127.0.0.1:8000
```

### 4. 启动桌面客户端

另开第二个终端，在项目根目录运行：

```powershell
python -m desktop.app
```

也可以运行：

```powershell
python desktop/app.py
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

# 桌宠动画 Skill 升级路线

桌宠适合做成 Skill，但要拆清职责：

```text
pet-animation Skill：
  决定当前状态、动作、语音、渲染器、素材 id

Web / PySide / 未来桌面浮窗：
  负责真正播放 GIF / Spine / Live2D
```

也就是说，Skill 不直接画 UI，而是输出一份“动画指令”。

## 当前阶段：GIF MVP

当前已经把桌宠临时切换成 GIF：

```text
frontend/assets/pet-states/uta-live.gif
frontend/assets/pet-states/uta-live-alt.gif
```

后端 `pet_state` 预留字段：

```json
{
  "mood": "sunny",
  "animationState": "idle",
  "voiceLine": "我在旁边听着，状态正常。",
  "gesture": "idle-sway",
  "followUpHint": "点我一下也行，我会继续陪你待机。",
  "renderer": "gif",
  "assetId": "uta-live"
}
```

Web 前端用 `<img>` 直接播放 GIF。

PySide6 桌面端用 `QMovie` 播放 GIF。

## 下一阶段：多 GIF 状态

可以把不同状态拆成：

```text
idle.gif
happy.gif
think.gif
sing.gif
alert.gif
```

然后让 `animationState` 决定播放哪张 GIF。

## 再下一阶段：Spine / Live2D

未来可以把 `renderer` 从 `gif` 改成：

```text
spine
live2d
```

对应输出：

```json
{
  "renderer": "live2d",
  "assetId": "uta_live2d_v1",
  "animationState": "happy",
  "motion": "tap_body",
  "expression": "smile"
}
```

这样主聊天 Agent 仍然只关心“她现在是什么情绪和动作”，具体播放方式交给渲染器。

## 最推荐顺序

```text
1. 单 GIF 临时替换
2. 多 GIF 状态切换
3. 抽出 pet-animation Skill 执行函数
4. PySide6 中做桌宠浮窗
5. 接 Spine 或 Live2D 渲染器
```

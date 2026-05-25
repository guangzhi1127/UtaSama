# 自定义 Skills 接入说明

这里用于登记项目内部可被 Agent 调用的 Skills。

建议每个 Skill 至少包含：

- `id`: 唯一标识
- `displayName`: 显示名
- `category`: 能力分类
- `entry`: 调用入口
- `inputSchema`: 输入结构
- `outputSchema`: 输出结构
- `boundAgents`: 默认由哪些 Agent 使用
- `status`: `planned` / `ready` / `disabled`

后续可以把这里作为前端工作台、后端编排器和权限控制的共同配置源。


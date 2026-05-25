# 自定义 MCP 接入说明

这里用于登记后续要接入的自定义 MCP Server。

建议每个 MCP 至少声明：

- `id`: 唯一标识
- `displayName`: 显示名称
- `transport`: `stdio` / `http`
- `command`: 启动命令或服务地址
- `args`: 启动参数
- `env`: 环境变量占位
- `capabilities`: 对外暴露的能力
- `boundAgents`: 推荐绑定的 Agent

后续运行时可以按这个配置自动加载 MCP，并把可用能力同步给主 Agent 的路由层。


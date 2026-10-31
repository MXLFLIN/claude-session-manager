# PROGRESS · claude-session-manager

## 2026-10-31 初始版本

- 起因:用户问「Claude 有没有管理历史聊天记录的方法」,发现记录就是 `.claude\projects\*\<id>.jsonl`,官方只有 `--resume` / `-c` / `--fork-session`,`claude rm` 只管后台会话。
- 需求演进:CLI 脚本 → 「Win32 那种框框、要列表和搜索」→ 加深色标题栏 → 列表显示 **ai-title** 而不是首句。
- 实现:`sessions_gui.pyw`(tkinter,约 250 行,零依赖)
  - 扫描 `~/.claude/projects/*/*.jsonl`,跳过 `_回收站`
  - 标题优先 `ai-title`,否则第一句真实用户消息(跳过 `<system-reminder>` 和 tool_result)
  - 搜索即输即筛;双击详情;多选「移到回收站」
  - 高分屏缩放;DWM 深色标题栏
- GitHub:公开流程走了一遍(私有仓库),用户名 **MXLFLIN**。
- 已知可加:悬停显示首句、按项目分组、恢复功能(从 `_回收站` 搬回)。

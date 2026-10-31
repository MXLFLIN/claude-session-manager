# Claude 对话管理 (claude-session-manager)

一个 Windows 小工具,用列表 + 搜索来管理 **Claude Code 的历史对话**。

Claude Code 每次对话都存在本地的 `~/.claude/projects/<项目>/<会话id>.jsonl` 里,
文件名是一串 UUID,很难认出是哪次聊天。这个工具把它们列出来、能搜、能收进回收站。

## 功能

- 📋 列出所有历史对话:时间 / **标题** / 项目 / 消息数 / 大小
- 🏷 标题直接用 Claude 自己生成的那条(`ai-title`);没有生成过标题的,退回用第一句用户消息
- 🔍 搜索框边打边筛(匹配标题、首句、项目路径、日期)
- 🔁「打开回收站」切换到回收站列表,选中的对话可以「恢复此对话」搬回去
- ▶️ 选中后「打开此对话」才亮:新开一个终端并在原项目目录里 `claude --resume <id>` 接着聊
- 🗑 选中后「移到回收站」:_claude_session_recycle:文件搬进 `projects/_claude_session_recycle/`,不删除,可恢复
- 🖱 右键任意一行:移到回收站 / 打开此对话 / 打开文件位置(回收站里第一项变成「恢复此对话」)
- 📂 双击查看详情(标题、完整首句、路径、会话 ID)

## 用法

双击 **`ClaudeSessionManager.exe`** 即可(无黑窗)。

也支持双击 `sessions_gui.pyw`(需要 Python 3,无需第三方库)。

exe 是 `launcher.c` 编译出来的小启动器(约 65 KB),只负责用 `pythonw.exe` 打开同目录的 pyw;
所以 **exe 和 pyw 必须放在同一个文件夹**,且本机要装 Python。

命令行运行:

```bash
pythonw sessions_gui.pyw
```

## 注意

- 只读取本机的 Claude Code 记录,**不联网、不上传任何内容**。
- 「回收站」只是把 `.jsonl` 挪到 `_回收站` 文件夹,想恢复就搬回去。
- 如果某条对话正在使用中,建议先关掉再移动。

## 原理

每个 `.jsonl` 文件一行一条记录(JSON),工具只做了三件事:

1. 找到第一条真正的用户消息,当作标题;
2. 统计 `user` / `assistant` 消息条数;
3. 移动文件 = 让 Claude Code 的 `--resume` 列表里不再显示它。

## License

MIT

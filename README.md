# Claude 对话管理 (claude-session-manager)

一个 Windows 小工具,用列表加搜索管理 **Claude Code 的历史对话**。

Claude Code 每次对话都保存在本地 `~/.claude/projects/<项目>/<会话id>.jsonl`,
文件名是一串 UUID,无法直接辨认。这个工具把对话列成表格,支持搜索、排序、移入回收站和恢复。

[English](README.en.md)

## 功能

- 列出所有对话:时间、标题、项目、消息数、大小
- 标题取自 Claude 生成的 `ai-title`;没有生成过标题的,使用第一句用户消息
- 搜索框边输入边筛选(标题、首句、项目路径、日期)
- 点击列标题排序,再次点击反向
- 每 30 秒静默刷新一次,并保留当前选中项
- 「打开回收站」把列表切换到回收站内容,选中的对话可以恢复回原项目目录
- 「打开此对话」在新终端中原项目目录执行 `claude --resume <会话id>`
- 「移到回收站」把文件移入 `projects/_claude_session_recycle/`,不删除,可恢复
- 右键任意一行:打开此对话、移到回收站、打开文件位置、详情
- 回收站视图的右键菜单多一项红色「彻底删除此对话」,二次确认后从磁盘删除
- 移入回收站前检查最近 60 秒内的写入,可能正在使用的对话会先给出提示
- 双击一行查看详情(标题、完整首句、路径、会话 ID)
- 界面支持中文和 English,可在「配置」中即时切换
- 配置窗口中可一键打开 `~/.claude/CLAUDE.md`

## 用法

双击 **`ClaudeSessionManager.exe`**(不出现控制台窗口)。

也可以双击 `sessions_gui.pyw`(需要 Python 3,无需第三方库)。

exe 由 `launcher.c` 编译而成(约 65 KB),作用是用 `pythonw.exe` 启动同目录下的 pyw 文件。
因此 exe 与 pyw 必须放在同一文件夹,且本机需要安装 Python。

命令行:

```bash
pythonw sessions_gui.pyw
```

## 注意

- 只读取本机的 Claude Code 记录,不联网,不上传任何内容。
- 「回收站」指把文件移动到 `projects/_claude_session_recycle/`;恢复时移回 `projects/<项目>/`。
- 移入回收站针对的是 Claude Code 的会话文件;打开对话需要本机可执行 `claude` 命令。
- 正在使用的对话文件可能持续写入,移动前建议先结束该对话。

## 原理

每个 `.jsonl` 文件一行是一条 JSON 记录,工具主要做三件事:

1. 找到第一条真正的用户消息,在没有 `ai-title` 时作为标题;
2. 统计 `user` 与 `assistant` 记录条数;
3. 在项目目录与回收站目录之间移动文件;Claude Code 的 `--resume` 只显示项目目录内的会话。

## License

MIT

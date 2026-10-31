# -*- coding: utf-8 -*-
"""Claude 对话管理 —— 列出、搜索、回收 Claude Code 的历史对话。

数据来源: C:\\Users\\mobai\\.claude\\projects\\<项目>\\<会话id>.jsonl
“移到回收站” = 把文件搬进 projects\\_回收站\\ 下, 不删除, 可随时搬回来。
"""
import ctypes
import json
import os
import re
import shutil
import subprocess
import threading
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

try:  # 高分屏不糊
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

PROJECTS_ROOT = Path.home() / ".claude" / "projects"
RECYCLE_NAME = "_回收站"


# ---------- 读数据 ----------
def message_text(msg):
    """从 message.content 里取出纯文本; 工具结果等非人话内容返回空。"""
    content = msg.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [b.get("text", "") for b in content
                 if isinstance(b, dict) and b.get("type") == "text"]
        return "\n".join(parts)
    return ""


def scan_sessions():
    sessions = []
    if not PROJECTS_ROOT.exists():
        return sessions
    for f in PROJECTS_ROOT.glob("*/*.jsonl"):
        if f.parent.name == RECYCLE_NAME:
            continue
        title, first, count, cwd = "", "", 0, ""
        try:
            with f.open(encoding="utf-8", errors="ignore") as fh:
                for line in fh:
                    try:
                        d = json.loads(line)
                    except Exception:
                        continue
                    if not cwd and d.get("cwd"):
                        cwd = d["cwd"]
                    if d.get("isSidechain"):
                        continue
                    if d.get("type") in ("user", "assistant"):
                        count += 1
                    if d.get("type") == "ai-title" and d.get("aiTitle"):
                        title = d["aiTitle"]      # AI 生成的对话标题
                    if not first and d.get("type") == "user":
                        t = message_text(d.get("message") or {}).strip()
                        # 跳过 <system-reminder>、命令输出这类不是人说的话
                        if t and not t.startswith("<"):
                            first = " ".join(t.split())[:200]
        except OSError:
            continue
        if count == 0:
            continue
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        sessions.append({
            "path": f,
            "sid": f.stem,
            "project": f.parent.name,
            "cwd": cwd,
            "title": title or first[:80] or "(无标题)",
            "first": first,
            "count": count,
            "size": f.stat().st_size,
            "mtime": mtime,
        })
    sessions.sort(key=lambda s: s["mtime"], reverse=True)
    return sessions


def human_size(n):
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.0f} KB"
    return f"{n / 1024 / 1024:.1f} MB"


def project_label(name):
    """C--Users-mobai -> C:\\Users\\mobai"""
    if "--" in name:
        drive, rest = name.split("--", 1)
        return drive + ":\\" + rest.replace("-", "\\")
    return name


# ---------- 窗口 ----------
class App:
    def __init__(self, root, dpi=96):
        self.root = root
        self.scale = dpi / 96.0
        self.data = []
        self.shown = []
        root.title("Claude 对话管理")
        root.geometry(f"{int(920 * self.scale)}x{int(560 * self.scale)}")
        root.minsize(int(700 * self.scale), int(380 * self.scale))

        base = ttk.Frame(root, padding=(10, 8, 10, 6))
        base.pack(fill="both", expand=True)

        # 顶部: 搜索 + 刷新
        top = ttk.Frame(base)
        top.pack(fill="x", pady=(0, 6))
        ttk.Button(top, text="刷新", command=self.load).pack(side="right")
        ttk.Button(top, text="清空", command=lambda: self.q.set("")).pack(side="right", padx=(0, 6))
        ttk.Label(top, text="搜索").pack(side="left")
        self.q = tk.StringVar()
        self.q.trace_add("write", lambda *_: self.refresh_view())
        entry = ttk.Entry(top, textvariable=self.q)
        entry.pack(side="left", fill="x", expand=True, padx=(6, 6))

        # 列表
        cols = ("time", "title", "project", "count", "size")
        self.tree = ttk.Treeview(base, columns=cols, show="headings", selectmode="extended")
        for c, text, w, anchor in (
            ("time", "时间", 120, "w"),
            ("title", "标题", 380, "w"),
            ("project", "项目", 200, "w"),
            ("count", "消息数", 70, "e"),
            ("size", "大小", 70, "e"),
        ):
            self.tree.heading(c, text=text)
            self.tree.column(c, width=int(w * self.scale), anchor=anchor,
                             stretch=(c == "title"))
        sb = ttk.Scrollbar(base, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")

        # 斑马纹 + 行高
        self.tree.tag_configure("odd", background="#f4f6f8")
        try:
            import tkinter.font as tkfont
            row = tkfont.nametofont("TkDefaultFont").metrics("linespace")
            ttk.Style().configure("Treeview", rowheight=row + 10)
        except Exception:
            pass

        self.tree.bind("<Double-1>", self.show_detail)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # 底部按钮 + 状态
        bottom = ttk.Frame(root, padding=(10, 0, 10, 8))
        bottom.pack(fill="x")
        self.open_btn = ttk.Button(bottom, text="打开此对话", command=self.open_session,
                                   state="disabled")
        self.open_btn.pack(side="left")
        ttk.Button(bottom, text="移到回收站", command=self.recycle).pack(side="left", padx=(6, 0))
        ttk.Button(bottom, text="打开所在文件夹", command=self.open_folder).pack(side="left", padx=6)
        self.status = ttk.Label(bottom, text="")
        self.status.pack(side="right")

        self.load()

    # ----- 加载 -----
    def load(self):
        self.status.config(text="正在读取…")
        threading.Thread(target=self._load_worker, daemon=True).start()

    def _load_worker(self):
        data = scan_sessions()
        self.root.after(0, lambda: self._loaded(data))

    def _loaded(self, data):
        self.data = data
        self.refresh_view()

    # ----- 过滤 + 画表 -----
    def refresh_view(self):
        q = self.q.get().strip().lower()
        self.shown = []
        for s in self.data:
            hay = f"{s['title']} {s['first']} {s['cwd'] or project_label(s['project'])} {s['mtime']:%Y-%m-%d %H:%M}".lower()
            if not q or q in hay:
                self.shown.append(s)

        self.tree.delete(*self.tree.get_children())
        for i, s in enumerate(self.shown):
            self.tree.insert("", "end", iid=str(i), tags=("odd",) if i % 2 else (), values=(
                s["mtime"].strftime("%m-%d %H:%M"),
                s["title"],
                s["cwd"] or project_label(s["project"]),
                s["count"],
                human_size(s["size"]),
            ))
        self.status.config(text=f"共 {len(self.data)} 条, 筛出 {len(self.shown)} 条")
        self._on_select()

    def selected(self):
        return [self.shown[int(i)] for i in self.tree.selection()]

    # ----- 操作 -----
    def _on_select(self, _event=None):
        """选中东西时「打开此对话」才亮, 否则灰着。"""
        self.open_btn.state(["!disabled"] if self.tree.selection() else ["disabled"])

    def open_session(self):
        items = self.selected()
        if not items:
            return
        s = items[0]
        sid = s["sid"]
        if not re.fullmatch(r"[0-9a-fA-F-]{8,}", sid):
            messagebox.showerror("打开失败", "会话 ID 看起来不对, 不敢拼进命令里。")
            return
        kwargs = {}
        cwd = s.get("cwd") or ""
        if cwd and Path(cwd).is_dir():
            kwargs["cwd"] = cwd
        env = os.environ.copy()
        # 别把「我是 Claude 派生的子会话」这个标记传给新会话, 否则它不保存聊天记录
        for key in ("CLAUDE_CODE_CHILD_SESSION", "CLAUDE_CODE_ENTRYPOINT"):
            env.pop(key, None)
        try:
            subprocess.Popen(
                ["cmd", "/k", f"chcp 65001>nul & claude --resume {sid}"],
                creationflags=subprocess.CREATE_NEW_CONSOLE, env=env, **kwargs)
        except OSError as e:
            messagebox.showerror("打开失败", str(e))

    def recycle(self):
        items = self.selected()
        if not items:
            messagebox.showinfo("提示", "先选中要处理的对话(可按住 Ctrl 多选)。")
            return
        preview = items[0]["title"][:40]
        more = f" 等 {len(items)} 条" if len(items) > 1 else ""
        if not messagebox.askyesno(
                "移到回收站",
                f"确定把「{preview}」{more} 移到回收站?\n\n"
                "文件不会删除, 只是从对话列表里藏起来, 以后能搬回来。"):
            return
        dest_root = PROJECTS_ROOT / RECYCLE_NAME
        moved = 0
        for s in items:
            dest_dir = dest_root / s["project"]
            dest_dir.mkdir(parents=True, exist_ok=True)
            try:
                target = dest_dir / s["path"].name
                if target.exists():
                    target = dest_dir / f"{s['sid']}_{datetime.now():%H%M%S}.jsonl"
                shutil.move(str(s["path"]), str(target))
                sub = s["path"].with_suffix("")  # 同名文件夹(子代理记录)
                if sub.is_dir():
                    shutil.move(str(sub), str(dest_dir / sub.name))
                moved += 1
            except OSError as e:
                messagebox.showerror("搬移失败", f"{s['path'].name}\n{e}")
        if moved:
            self.load()

    def open_folder(self):
        items = self.selected()
        target = items[0]["path"] if items else PROJECTS_ROOT
        subprocess.Popen(["explorer", "/select,", str(target)])

    def show_detail(self, _event=None):
        items = self.selected()
        if not items:
            return
        s = items[0]
        win = tk.Toplevel(self.root)
        win.title("对话详情")
        win.geometry("640x420")
        body = ttk.Frame(win, padding=12)
        body.pack(fill="both", expand=True)
        rows = [
            ("标题", s["title"]),
            ("首句", s["first"] or "(无)"),
            ("项目", s["cwd"] or project_label(s["project"])),
            ("时间", s["mtime"].strftime("%Y-%m-%d %H:%M:%S")),
            ("消息数", str(s["count"])),
            ("大小", human_size(s["size"])),
            ("路径", str(s["path"])),
            ("会话 ID", s["sid"]),
        ]
        for r, (k, v) in enumerate(rows):
            ttk.Label(body, text=k).grid(row=r, column=0, sticky="nw", pady=3)
            ttk.Label(body, text=v, wraplength=520, justify="left").grid(
                row=r, column=1, sticky="nw", padx=(10, 0), pady=3)
        body.columnconfigure(1, weight=1)
        ttk.Button(body, text="关闭", command=win.destroy).grid(
            row=len(rows), column=1, sticky="e", pady=(10, 0))


def enable_dark_titlebar(root):
    """把标题栏涂成和 cmd 窗口一样的深色。"""
    try:
        root.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        on = ctypes.c_int(1)
        for attr in (20, 19):  # Win10 20H1+ 用 20, 更老的用 19
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, attr, ctypes.byref(on), ctypes.sizeof(on))
    except Exception:
        pass


def main():
    root = tk.Tk()
    try:
        dpi = ctypes.windll.user32.GetDpiForSystem()
        root.tk.call("tk", "scaling", dpi / 72.0)
    except Exception:
        dpi = 96
    try:
        ttk.Style().theme_use("vista")
    except Exception:
        pass
    App(root, dpi)
    root.after(300, enable_dark_titlebar, root)   # 等窗口真正显示后再涂色
    root.mainloop()


if __name__ == "__main__":
    main()

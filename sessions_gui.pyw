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
import time
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

try:  # 高分屏不糊
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

PROJECTS_ROOT = Path.home() / ".claude" / "projects"
RECYCLE_NAME = "_claude_session_recycle"
CONFIG_PATH = Path.home() / ".claude" / "claude-session-manager.json"
CACHE_PATH = Path.home() / ".claude" / "claude-session-manager-cache.json"
MEMORY_PATH = Path.home() / ".claude" / "CLAUDE.md"

TR = {
    "zh": {
        "app_title": "Claude 对话管理",
        "search": "搜索", "refresh": "刷新", "clear": "清空",
        "col_time": "时间", "col_title": "标题", "col_project": "项目",
        "col_count": "消息数", "col_size": "大小",
        "settings": "配置", "language": "语言",
        "open_memory": "打开 Claude Code 全局记忆文件",
        "clear_cache": "清除缓存", "cache_cleared": "缓存已清除, 下次读取会重新解析全部会话。",
        "memory_missing": "找不到全局记忆文件",
        "close": "关闭",
        "open_recycle": "打开回收站", "open_list": "打开会话列表",
        "btn_open": "打开此对话", "btn_new": "打开新对话",
        "new_dir": "新对话默认目录", "browse": "浏览",
        "recycled_prefix": "回收站 · ",
        "status": "共 {total} 条, 筛出 {shown} 条",
        "menu_open": "打开此对话", "menu_recycle": "移到回收站",
        "menu_restore": "恢复此对话", "menu_folder": "打开文件位置",
        "menu_purge": "彻底删除此对话", "menu_detail": "详情",
        "detail_title": "对话详情", "d_title": "标题", "d_first": "首句",
        "d_project": "项目", "d_time": "时间", "d_count": "消息数",
        "d_size": "大小", "d_path": "路径", "d_sid": "会话 ID",
        "d_none": "(无)",
        "hint_select": "先选中要处理的对话(可按住 Ctrl 多选)。",
        "more": " 等 {n} 条",
        "recycle_title": "移到回收站",
        "recycle_msg": "确定把「{preview}」{more} 移到回收站?{nl}{nl}文件将不会被彻底删除, 将会移动到回收站文件夹, 以后可以恢复。{nl}{nl}回收站位置: {path}",
        "purge_title": "彻底删除",
        "purge_msg": "您是否要删除「{preview}」{more}?{nl}{nl}这将会使此对话从你的磁盘中永久删除,是否确认?",
        "err_open": "打开失败", "err_move": "搬移失败",
        "err_restore": "恢复失败", "err_delete": "删除失败",
        "err_badid": "会话 ID 看起来不对, 不敢拼进命令里。",
        "loading": "正在读取…",
        "warn_title": "检测到正在使用的对话",
        "warn_active": "有 {n} 条对话在最近 60 秒内仍有写入, 可能正在使用中。仍要移入回收站吗?",
    },
    "en": {
        "app_title": "Claude Session Manager",
        "search": "Search", "refresh": "Refresh", "clear": "Clear",
        "col_time": "Time", "col_title": "Title", "col_project": "Project",
        "col_count": "Messages", "col_size": "Size",
        "settings": "Settings", "language": "Language",
        "open_memory": "Open Claude Code global memory file",
        "clear_cache": "Clear cache", "cache_cleared": "Cache cleared. The next load will re-scan every session.",
        "memory_missing": "Global memory file not found",
        "close": "Close",
        "open_recycle": "Open Recycle Bin", "open_list": "Back to Sessions",
        "btn_open": "Open session", "btn_new": "New session",
        "new_dir": "New session folder", "browse": "Browse",
        "recycled_prefix": "Recycle Bin | ",
        "status": "{total} sessions, {shown} shown",
        "menu_open": "Open session", "menu_recycle": "Move to Recycle Bin",
        "menu_restore": "Restore session", "menu_folder": "Show in folder",
        "menu_purge": "Delete permanently", "menu_detail": "Details",
        "detail_title": "Session details", "d_title": "Title", "d_first": "First message",
        "d_project": "Project", "d_time": "Time", "d_count": "Messages",
        "d_size": "Size", "d_path": "Path", "d_sid": "Session ID",
        "d_none": "(none)",
        "hint_select": "Select a session first (Ctrl-click to pick several).",
        "more": " and {n} more",
        "recycle_title": "Move to Recycle Bin",
        "recycle_msg": "Move \"{preview}\"{more} to the Recycle Bin?{nl}{nl}The file is NOT deleted. It is moved into the recycle folder and can be restored later.{nl}{nl}Location: {path}",
        "purge_title": "Delete permanently",
        "purge_msg": "Delete \"{preview}\"{more}?{nl}{nl}This permanently removes the session from your disk. Continue?",
        "err_open": "Cannot open", "err_move": "Move failed",
        "err_restore": "Restore failed", "err_delete": "Delete failed",
        "err_badid": "The session ID looks invalid; refusing to run it.",
        "loading": "Loading...",
        "warn_title": "Active session detected",
        "warn_active": "{n} session(s) were written to within the last 60 seconds and may still be in use. Move to Recycle Bin anyway?",
    },
}


def load_config():
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_config(cfg):
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2),
                               encoding="utf-8")
    except OSError:
        pass


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


def load_cache():
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_cache(cache):
    try:
        CACHE_PATH.write_text(json.dumps(cache), encoding="utf-8")
    except OSError:
        pass


def scan_sessions(include_recycle=False):
    """扫描会话文件。文件没变时直接使用上次的解析结果。"""
    sessions = []
    base = (PROJECTS_ROOT / RECYCLE_NAME) if include_recycle else PROJECTS_ROOT
    if not base.exists():
        return sessions
    cache = load_cache()
    dirty = False
    for f in base.glob("*/*.jsonl"):
        if not include_recycle and f.parent.name == RECYCLE_NAME:
            continue
        try:
            st = f.stat()
        except OSError:
            continue
        key = str(f)
        hit = cache.get(key)
        if hit and hit.get("mtime") == st.st_mtime and hit.get("size") == st.st_size:
            title = hit.get("title", "")
            first = hit.get("first", "")
            cwd = hit.get("cwd", "")
            count = hit.get("count", 0)
        else:
            try:
                raw = f.read_bytes()
            except OSError:
                continue
            count = raw.count(b'"type":"user"') + raw.count(b'"type":"assistant"')
            count -= raw.count(b'"isSidechain":true')
            title, first, cwd = "", "", ""
            for line in raw.split(bytes([10])):
                if b'"type":"ai-title"' in line:
                    try:
                        v = json.loads(line).get("aiTitle")
                        if v:
                            title = v
                    except Exception:
                        pass
                    continue
                if not cwd and b'"cwd":"' in line:
                    try:
                        cwd = json.loads(line).get("cwd") or ""
                    except Exception:
                        pass
                if not first and b'"type":"user"' in line and b'"isSidechain":true' not in line:
                    try:
                        t = message_text(json.loads(line).get("message") or {}).strip()
                    except Exception:
                        t = ""
                    if t and not t.startswith("<"):
                        first = " ".join(t.split())[:200]
            cache[key] = {"mtime": st.st_mtime, "size": st.st_size,
                          "title": title, "first": first, "cwd": cwd, "count": count}
            dirty = True
        if count <= 0:
            continue
        sessions.append({
            "path": f,
            "sid": f.stem,
            "project": f.parent.name,
            "cwd": cwd,
            "title": title or first[:80] or "(无标题)",
            "first": first,
            "count": count,
            "size": st.st_size,
            "mtime": datetime.fromtimestamp(st.st_mtime),
            "recycled": include_recycle,
        })
    if dirty:
        save_cache(cache)
    sessions.sort(key=lambda x: x["mtime"], reverse=True)
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


def migrate_old_recycle():
    """老版本用的中文目录名, 启动时并到新目录里。"""
    old = PROJECTS_ROOT / "_回收站"
    new = PROJECTS_ROOT / RECYCLE_NAME
    if not old.is_dir():
        return
    new.mkdir(parents=True, exist_ok=True)
    for child in old.iterdir():
        dest = new / child.name
        if dest.exists():
            continue
        try:
            shutil.move(str(child), str(dest))
        except OSError:
            pass
    try:
        old.rmdir()
    except OSError:
        pass


# ---------- 窗口 ----------
class App:
    def __init__(self, root, dpi=96):
        self.root = root
        self.scale = dpi / 96.0
        self.data = []
        self.shown = []
        self.mode = "active"          # active = 会话列表, recycle = 回收站
        self.cfg = load_config()
        self.lang = self.cfg.get("lang", "en")
        self._settings_win = None
        self.sort_col = "time"
        self.sort_desc = True
        self._auto_job = None
        root.title(self.t("app_title"))
        w, h = int(920 * self.scale), int(560 * self.scale)
        x = max(0, (root.winfo_screenwidth() - w) // 2)
        y = max(0, (root.winfo_screenheight() - h) // 2)
        root.geometry(f"{w}x{h}+{x}+{y}")
        root.minsize(int(700 * self.scale), int(380 * self.scale))

        base = ttk.Frame(root, padding=(10, 8, 10, 6))
        base.pack(fill="both", expand=True)

        # 顶部: 搜索 + 刷新
        top = ttk.Frame(base)
        top.pack(fill="x", pady=(0, 6))
        self.btn_refresh = ttk.Button(top, text=self.t("refresh"), command=self.load)
        self.btn_refresh.pack(side="right")
        self.btn_clear = ttk.Button(top, text=self.t("clear"),
                                    command=lambda: self.q.set(""))
        self.btn_clear.pack(side="right", padx=(0, 6))
        self.lbl_search = ttk.Label(top, text=self.t("search"))
        self.lbl_search.pack(side="left")
        self.q = tk.StringVar()
        self.q.trace_add("write", lambda *_: self.refresh_view())
        entry = ttk.Entry(top, textvariable=self.q)
        entry.pack(side="left", fill="x", expand=True, padx=(6, 6))

        # 列表
        cols = ("time", "title", "project", "count", "size")
        self.tree = ttk.Treeview(base, columns=cols, show="headings", selectmode="extended")
        for c, key, w, anchor in (
            ("time", "col_time", 120, "w"),
            ("title", "col_title", 380, "w"),
            ("project", "col_project", 200, "w"),
            ("count", "col_count", 70, "e"),
            ("size", "col_size", 70, "e"),
        ):
            self.tree.heading(c, text=self.t(key),
                              command=lambda col=c: self.sort_by(col))
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

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Button-1>", self._on_click)
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-3>", self._popup)      # 右键菜单

        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label=self.t("menu_open"), command=self.open_session)
        self.menu.add_command(label=self.t("menu_recycle"), command=self.recycle)
        self.menu.add_command(label=self.t("menu_folder"), command=self.open_folder)
        self.menu.add_separator()
        self.menu.add_command(label=self.t("menu_detail"), command=self.show_detail)
        self._has_delete = False      # 「彻底删除」只在回收站视图里临时插进来

        # 底部按钮 + 状态
        bottom = ttk.Frame(root, padding=(10, 0, 10, 8))
        bottom.pack(fill="x")
        self.btn_settings = ttk.Button(bottom, text=self.t("settings"),
                                       command=self.open_settings)
        self.btn_settings.pack(side="left")
        self.mode_btn = ttk.Button(bottom, text=self.t("open_recycle"),
                                   command=self.toggle_mode)
        self.mode_btn.pack(side="left", padx=(6, 0))
        self.btn_open = ttk.Button(bottom, text=self.t("btn_open"),
                                   command=self.open_session, state="disabled")
        self.btn_open.pack(side="left", padx=(6, 0))
        self.btn_new = ttk.Button(bottom, text=self.t("btn_new"),
                                  command=self.new_session)
        self.btn_new.pack(side="left", padx=(6, 0))
        self.status = ttk.Label(bottom, text="")
        self.status.pack(side="right")

        self._update_headings()
        self.load()
        self._schedule_auto()

    # ----- 加载 -----
    def load(self, silent=False):
        self.load_seq = getattr(self, "load_seq", 0) + 1
        seq, mode = self.load_seq, self.mode
        if not silent:
            self.status.config(text=self.t("loading"))
        threading.Thread(target=self._load_worker, args=(seq, mode), daemon=True).start()

    def _schedule_auto(self):
        """每 30 秒静默重读一次, 保持列表可信。"""
        if self._auto_job is None:
            self._auto_job = self.root.after(30000, self._auto_tick)

    def _auto_tick(self):
        self._auto_job = None
        self.load(silent=True)
        self._schedule_auto()

    def _load_worker(self, seq, mode):
        data = scan_sessions(mode == "recycle")
        self.root.after(0, lambda: self._loaded(seq, mode, data))

    def _loaded(self, seq, mode, data):
        # 快速切换视图时, 旧线程的结果可能后到 —— 不是当前这次请求就丢掉
        if seq != getattr(self, "load_seq", seq) or mode != self.mode:
            return
        keep = {x["sid"] for x in self.selected()}
        self.data = data
        self.refresh_view()
        if keep:
            for i, x in enumerate(self.shown):
                if x["sid"] in keep:
                    self.tree.selection_add(self.tree.get_children()[i])

    # ----- 过滤 + 画表 -----
    def _sort_key(self, x):
        col = self.sort_col
        if col == "time":
            return x["mtime"]
        if col == "count":
            return x["count"]
        if col == "size":
            return x["size"]
        if col == "project":
            return (x["cwd"] or project_label(x["project"])).lower()
        return (x["title"] or "").lower()

    def _update_headings(self):
        arrow = " \u2193" if self.sort_desc else " \u2191"
        for c, key in (("time", "col_time"), ("title", "col_title"),
                       ("project", "col_project"), ("count", "col_count"),
                       ("size", "col_size")):
            self.tree.heading(c, text=self.t(key) + (arrow if c == self.sort_col else ""))

    def sort_by(self, col):
        if col == self.sort_col:
            self.sort_desc = not self.sort_desc
        else:
            self.sort_col = col
            self.sort_desc = col in ("time", "count", "size")
        self._update_headings()
        self.refresh_view()

    def refresh_view(self):
        q = self.q.get().strip().lower()
        self.shown = []
        for s in self.data:
            hay = f"{s['title']} {s['first']} {s['cwd'] or project_label(s['project'])} {s['mtime']:%Y-%m-%d %H:%M}".lower()
            if not q or q in hay:
                self.shown.append(s)
        self.shown.sort(key=self._sort_key, reverse=self.sort_desc)

        self.tree.delete(*self.tree.get_children())
        for i, s in enumerate(self.shown):
            self.tree.insert("", "end", iid=str(i), tags=("odd",) if i % 2 else (), values=(
                s["mtime"].strftime("%m-%d %H:%M"),
                s["title"],
                s["cwd"] or project_label(s["project"]),
                s["count"],
                human_size(s["size"]),
            ))
        prefix = self.t("recycled_prefix") if self.mode == "recycle" else ""
        self.status.config(text=prefix + self.t(
            "status", total=len(self.data), shown=len(self.shown)))
        self._on_select()

    def selected(self):
        return [self.shown[int(i)] for i in self.tree.selection()]

    def _on_select(self, _event=None):
        """只有会话列表里选中了东西, 「打开此对话」才可用。"""
        ok = self.mode == "active" and bool(self.tree.selection())
        self.btn_open.state(["!disabled"] if ok else ["disabled"])

    def _on_click(self, event):
        """点空白处 = 取消选中。"""
        if not self.tree.identify_row(event.y):
            self.tree.selection_remove(self.tree.selection())

    def _on_double_click(self, event):
        """只有真的双击在某一行上才打开详情。"""
        row = self.tree.identify_row(event.y)
        if not row:
            return
        self.tree.selection_set(row)
        self.show_detail()

    def _popup(self, event):
        row = self.tree.identify_row(event.y)
        if not row:
            return
        if row not in self.tree.selection():
            self.tree.selection_set(row)
        self.tree.focus(row)
        # 回收站视图里第一项换成「恢复此对话」
        if self.mode == "recycle":
            self.menu.entryconfigure(1, label=self.t("menu_restore"),
                                     command=self.restore_session)
            if not self._has_delete:
                self.menu.insert_command(
                    4, label=self.t("menu_purge"), foreground="red",
                    command=self.purge_session)
                self._has_delete = True
        else:
            self.menu.entryconfigure(1, label=self.t("menu_recycle"),
                                     command=self.recycle)
            if self._has_delete:
                self.menu.delete(4)
                self._has_delete = False
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    # ----- 操作 -----
    def t(self, key, **kw):
        text = TR.get(self.lang, TR["zh"]).get(key, key)
        text = text.replace("{nl}", chr(10))   # 先换行, 再格式化(否则 format 不认识 {nl})
        if kw:
            text = text.format(**kw)
        return text

    def open_settings(self):
        if self._settings_win and self._settings_win.winfo_exists():
            self._settings_win.lift()
            return
        win = self._settings_win = tk.Toplevel(self.root)
        win.title(self.t("settings"))
        win.transient(self.root)
        win.geometry("580x240")
        win.resizable(False, False)
        body = ttk.Frame(win, padding=14)
        body.pack(fill="both", expand=True)
        self._set_win = win
        self._set_lbl = ttk.Label(body, text=self.t("language"))
        self._set_lbl.grid(row=0, column=0, sticky="w")
        combo = self._set_combo = ttk.Combobox(body, values=["中文", "English"],
                                               state="readonly", width=14)
        combo.set("English" if self.lang == "en" else "中文")
        combo.grid(row=0, column=1, sticky="w", padx=(10, 0))
        combo.bind("<<ComboboxSelected>>",
                   lambda e: self.set_language("en" if combo.get() == "English" else "zh"))
        self._set_lbl_dir = ttk.Label(body, text=self.t("new_dir"))
        self._set_lbl_dir.grid(row=1, column=0, sticky="w", pady=(12, 0))
        self._set_dir = tk.StringVar(
            value=self.cfg.get("new_session_dir") or str(Path.home()))
        ent = ttk.Entry(body, textvariable=self._set_dir, width=38)
        ent.grid(row=1, column=1, columnspan=2, sticky="we", padx=(10, 6), pady=(12, 0))
        ent.bind("<FocusOut>", lambda e: self._save_dir())
        ent.bind("<Return>", lambda e: self._save_dir())
        self._set_btn_browse = ttk.Button(body, text=self.t("browse"),
                                          command=self._pick_dir, width=9)
        self._set_btn_browse.grid(row=1, column=3, sticky="e", pady=(12, 0))
        row2 = ttk.Frame(body)
        row2.grid(row=2, column=0, columnspan=4, sticky="w", pady=(16, 0))
        self._set_btn_mem = ttk.Button(row2, text=self.t("open_memory"),
                                       command=self.open_memory)
        self._set_btn_mem.pack(side="left")
        self._set_btn_cache = ttk.Button(row2, text=self.t("clear_cache"),
                                         command=self.clear_cache)
        self._set_btn_cache.pack(side="left", padx=(10, 0))
        self._set_btn_close = ttk.Button(body, text=self.t("close"), command=win.destroy)
        self._set_btn_close.grid(row=3, column=3, sticky="e", pady=(16, 0))
        win.update_idletasks()
        px, py = self.root.winfo_rootx(), self.root.winfo_rooty()
        pw, ph = self.root.winfo_width(), self.root.winfo_height()
        win.geometry(f"+{px + (pw - win.winfo_width()) // 2}+{py + (ph - win.winfo_height()) // 2}")
        body.columnconfigure(1, weight=1)
        body.columnconfigure(2, weight=0)

    def clear_cache(self):
        try:
            CACHE_PATH.unlink(missing_ok=True)
        except OSError:
            pass
        messagebox.showinfo(self.t("settings"), self.t("cache_cleared"))
        self.load()

    def _pick_dir(self):
        start = self._set_dir.get() or str(Path.home())
        d = filedialog.askdirectory(initialdir=start, parent=self._settings_win)
        if d:
            self._set_dir.set(d)
            self._save_dir()

    def _save_dir(self):
        raw = self._set_dir.get().strip()
        if raw and not Path(raw).is_dir():
            return
        self.cfg["new_session_dir"] = raw or str(Path.home())
        save_config(self.cfg)

    def set_language(self, lang):
        self.lang = lang
        self.cfg["lang"] = lang
        save_config(self.cfg)
        self.apply_language()

    def apply_language(self):
        self.root.title(self.t("app_title"))
        self.lbl_search.configure(text=self.t("search"))
        self.btn_clear.configure(text=self.t("clear"))
        self.btn_refresh.configure(text=self.t("refresh"))
        self.btn_settings.configure(text=self.t("settings"))
        self.btn_open.configure(text=self.t("btn_open"))
        self.btn_new.configure(text=self.t("btn_new"))
        self.mode_btn.configure(text=self.t("open_recycle")
                                if self.mode == "active" else self.t("open_list"))
        self._update_headings()
        self.menu.entryconfigure(0, label=self.t("menu_open"))
        self.menu.entryconfigure(1, label=self.t("menu_restore")
                                 if self.mode == "recycle" else self.t("menu_recycle"))
        self.menu.entryconfigure(2, label=self.t("menu_folder"))
        self.menu.entryconfigure(self.menu.index("end"), label=self.t("menu_detail"))
        self.refresh_view()
        if self._settings_win and self._settings_win.winfo_exists():
            self._settings_win.title(self.t("settings"))
            self._set_lbl.configure(text=self.t("language"))
            self._set_btn_mem.configure(text=self.t("open_memory"))
            self._set_btn_cache.configure(text=self.t("clear_cache"))
            self._set_lbl_dir.configure(text=self.t("new_dir"))
            self._set_btn_browse.configure(text=self.t("browse"))
            self._set_btn_close.configure(text=self.t("close"))

    def open_memory(self):
        if MEMORY_PATH.exists():
            os.startfile(str(MEMORY_PATH))
        else:
            messagebox.showinfo(self.t("settings"),
                                self.t("memory_missing") + ": " + str(MEMORY_PATH))

    def open_session(self):
        items = self.selected()
        if not items:
            return
        s = items[0]
        sid = s["sid"]
        if not re.fullmatch(r"[0-9a-fA-F-]{8,}", sid):
            messagebox.showerror(self.t("err_open"), self.t("err_badid"))
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
            messagebox.showerror(self.t("err_open"), str(e))

    def new_session(self):
        """在默认目录启动一个新的 claude 会话。"""
        cwd = self.cfg.get("new_session_dir") or str(Path.home())
        if not Path(cwd).is_dir():
            cwd = str(Path.home())
        env = os.environ.copy()
        for key in ("CLAUDE_CODE_CHILD_SESSION", "CLAUDE_CODE_ENTRYPOINT"):
            env.pop(key, None)
        try:
            subprocess.Popen(["cmd", "/k", "chcp 65001>nul & claude"],
                             cwd=cwd,
                             creationflags=subprocess.CREATE_NEW_CONSOLE,
                             env=env)
        except OSError as e:
            messagebox.showerror(self.t("err_open"), str(e))

    def recycle(self):
        if self.mode != "active":       # 双保险: 回收站视图里不能再回收
            return
        items = self.selected()
        if not items:
            messagebox.showinfo(self.t("settings"), self.t("hint_select"))
            return
        now = time.time()
        recent = [x for x in items if now - x["mtime"].timestamp() < 60]
        if recent:
            if not messagebox.askyesno(
                    self.t("warn_title"),
                    self.t("warn_active", n=len(recent)), icon="warning"):
                items = [x for x in items if x not in recent]
                if not items:
                    return
        preview = items[0]["title"][:40]
        more = self.t("more", n=len(items)) if len(items) > 1 else ""
        if not messagebox.askyesno(
                self.t("recycle_title"),
                self.t("recycle_msg", preview=preview, more=more,
                       path=PROJECTS_ROOT / RECYCLE_NAME)):
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
                messagebox.showerror(self.t("err_move"), s["path"].name + chr(10) + str(e))
        if moved:
            self.load()

    def open_folder(self):
        items = self.selected()
        target = items[0]["path"] if items else PROJECTS_ROOT
        subprocess.Popen(["explorer", "/select,", str(target)])

    def toggle_mode(self):
        """在主列表和回收站之间来回切。"""
        if self.mode == "active":
            self.mode = "recycle"
            self.mode_btn.configure(text=self.t("open_list"))
        else:
            self.mode = "active"
            self.mode_btn.configure(text=self.t("open_recycle"))
        self.q.set("")
        self.load()

    def restore_session(self):
        """把回收站里的对话搬回原来的项目文件夹。"""
        if self.mode != "recycle":      # 双保险: 只在回收站视图里才恢复
            return
        items = [x for x in self.selected()
                 if str(x["path"]).startswith(str(PROJECTS_ROOT / RECYCLE_NAME))]
        if not items:
            return
        restored = 0
        for s in items:
            dest_dir = PROJECTS_ROOT / s["project"]
            dest_dir.mkdir(parents=True, exist_ok=True)
            target = dest_dir / s["path"].name
            if target.exists():
                target = dest_dir / f"{s['sid']}_{datetime.now():%H%M%S}.jsonl"
            try:
                shutil.move(str(s["path"]), str(target))
                sub = s["path"].with_suffix("")   # 同名文件夹(子代理记录)
                if sub.is_dir():
                    shutil.move(str(sub), str(dest_dir / sub.name))
                restored += 1
            except OSError as e:
                messagebox.showerror(self.t("err_restore"), s["path"].name + chr(10) + str(e))
        if restored:
            self.load()

    def purge_session(self):
        """从回收站里永久删除(不进系统回收站)。"""
        if self.mode != "recycle":
            return
        items = [x for x in self.selected()
                 if str(x["path"]).startswith(str(PROJECTS_ROOT / RECYCLE_NAME))]
        if not items:
            return
        preview = items[0]["title"][:40]
        more = self.t("more", n=len(items)) if len(items) > 1 else ""
        if not messagebox.askyesno(
                self.t("purge_title"),
                self.t("purge_msg", preview=preview, more=more),
                icon="warning"):
            return
        for s in items:
            try:
                s["path"].unlink(missing_ok=True)
                sub = s["path"].with_suffix("")
                if sub.is_dir():
                    shutil.rmtree(sub, ignore_errors=True)
            except OSError as e:
                messagebox.showerror(self.t("err_delete"), s["path"].name + chr(10) + str(e))
        self.load()

    def show_detail(self, _event=None):
        items = self.selected()
        if not items:
            return
        s = items[0]
        win = tk.Toplevel(self.root)
        win.title(self.t("detail_title"))
        win.geometry("640x420")
        body = ttk.Frame(win, padding=12)
        body.pack(fill="both", expand=True)
        rows = [
            (self.t("d_title"), s["title"]),
            (self.t("d_first"), s["first"] or self.t("d_none")),
            (self.t("d_project"), s["cwd"] or project_label(s["project"])),
            (self.t("d_time"), s["mtime"].strftime("%Y-%m-%d %H:%M:%S")),
            (self.t("d_count"), str(s["count"])),
            (self.t("d_size"), human_size(s["size"])),
            (self.t("d_path"), str(s["path"])),
            (self.t("d_sid"), s["sid"]),
        ]
        for r, (k, v) in enumerate(rows):
            ttk.Label(body, text=k).grid(row=r, column=0, sticky="nw", pady=3)
            ttk.Label(body, text=v, wraplength=520, justify="left").grid(
                row=r, column=1, sticky="nw", padx=(10, 0), pady=3)
        body.columnconfigure(1, weight=1)
        ttk.Button(body, text=self.t("close"), command=win.destroy).grid(
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
    migrate_old_recycle()
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

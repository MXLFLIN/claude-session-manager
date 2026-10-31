# -*- coding: utf-8 -*-
"""一次性补丁:给工具加中英双语 + 配置窗口(改语言 / 打开全局记忆文件)。"""
import ast
from pathlib import Path

p = Path("sessions_gui.pyw")
s = p.read_text(encoding="utf-8")


def rep(old, new):
    global s
    assert old in s, "NOT FOUND: " + old[:70]
    s = s.replace(old, new, 1)


# ---------- 1. 常量 / 翻译表 / 配置 ----------
rep('''RECYCLE_NAME = "_claude_session_recycle"''',
'''RECYCLE_NAME = "_claude_session_recycle"
CONFIG_PATH = Path.home() / ".claude" / "claude-session-manager.json"
MEMORY_PATH = Path.home() / ".claude" / "CLAUDE.md"

TR = {
    "zh": {
        "app_title": "Claude 对话管理",
        "search": "搜索", "refresh": "刷新", "clear": "清空",
        "col_time": "时间", "col_title": "标题", "col_project": "项目",
        "col_count": "消息数", "col_size": "大小",
        "settings": "配置", "language": "语言",
        "open_memory": "打开 Claude Code 全局记忆文件",
        "memory_missing": "找不到全局记忆文件",
        "close": "关闭",
        "open_recycle": "打开回收站", "open_list": "打开会话列表",
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
    },
    "en": {
        "app_title": "Claude Session Manager",
        "search": "Search", "refresh": "Refresh", "clear": "Clear",
        "col_time": "Time", "col_title": "Title", "col_project": "Project",
        "col_count": "Messages", "col_size": "Size",
        "settings": "Settings", "language": "Language",
        "open_memory": "Open Claude Code global memory file",
        "memory_missing": "Global memory file not found",
        "close": "Close",
        "open_recycle": "Open Recycle Bin", "open_list": "Back to Sessions",
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
        "recycle_msg": "Move \\"{preview}\\"{more} to the Recycle Bin?{nl}{nl}The file is NOT deleted. It is moved into the recycle folder and can be restored later.{nl}{nl}Location: {path}",
        "purge_title": "Delete permanently",
        "purge_msg": "Delete \\"{preview}\\"{more}?{nl}{nl}This permanently removes the session from your disk. Continue?",
        "err_open": "Cannot open", "err_move": "Move failed",
        "err_restore": "Restore failed", "err_delete": "Delete failed",
        "err_badid": "The session ID looks invalid; refusing to run it.",
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
        pass''')

# ---------- 2. 语言状态 + 标题 ----------
rep('''        self.mode = "active"          # active = 会话列表, recycle = 回收站''',
'''        self.mode = "active"          # active = 会话列表, recycle = 回收站
        self.cfg = load_config()
        self.lang = self.cfg.get("lang", "zh")
        self._settings_win = None''')

rep('''        root.title("Claude 对话管理")''', '''        root.title(self.t("app_title"))''')

# ---------- 3. 顶部控件 ----------
rep('''        ttk.Button(top, text="刷新", command=self.load).pack(side="right")
        ttk.Button(top, text="清空", command=lambda: self.q.set("")).pack(side="right", padx=(0, 6))
        ttk.Label(top, text="搜索").pack(side="left")''',
'''        self.btn_refresh = ttk.Button(top, text=self.t("refresh"), command=self.load)
        self.btn_refresh.pack(side="right")
        self.btn_clear = ttk.Button(top, text=self.t("clear"),
                                    command=lambda: self.q.set(""))
        self.btn_clear.pack(side="right", padx=(0, 6))
        self.lbl_search = ttk.Label(top, text=self.t("search"))
        self.lbl_search.pack(side="left")''')

rep('''        for c, text, w, anchor in (
            ("time", "时间", 120, "w"),
            ("title", "标题", 380, "w"),
            ("project", "项目", 200, "w"),
            ("count", "消息数", 70, "e"),
            ("size", "大小", 70, "e"),
        ):
            self.tree.heading(c, text=text)''',
'''        for c, key, w, anchor in (
            ("time", "col_time", 120, "w"),
            ("title", "col_title", 380, "w"),
            ("project", "col_project", 200, "w"),
            ("count", "col_count", 70, "e"),
            ("size", "col_size", 70, "e"),
        ):
            self.tree.heading(c, text=self.t(key))''')

# ---------- 4. 底部按钮 ----------
rep('''        self.mode_btn = ttk.Button(bottom, text="打开回收站", command=self.toggle_mode)
        self.mode_btn.pack(side="left")''',
'''        self.btn_settings = ttk.Button(bottom, text=self.t("settings"),
                                       command=self.open_settings)
        self.btn_settings.pack(side="left")
        self.mode_btn = ttk.Button(bottom, text=self.t("open_recycle"),
                                   command=self.toggle_mode)
        self.mode_btn.pack(side="left", padx=(6, 0))''')

# ---------- 5. 菜单 ----------
rep('''        self.menu.add_command(label="打开此对话", command=self.open_session)
        self.menu.add_command(label="移到回收站", command=self.recycle)
        self.menu.add_command(label="打开文件位置", command=self.open_folder)
        self.menu.add_separator()
        self.menu.add_command(label="详情", command=self.show_detail)''',
'''        self.menu.add_command(label=self.t("menu_open"), command=self.open_session)
        self.menu.add_command(label=self.t("menu_recycle"), command=self.recycle)
        self.menu.add_command(label=self.t("menu_folder"), command=self.open_folder)
        self.menu.add_separator()
        self.menu.add_command(label=self.t("menu_detail"), command=self.show_detail)''')

rep('''        if self.mode == "recycle":
            self.menu.entryconfigure(1, label="恢复此对话", command=self.restore_session)
            if not self._has_delete:
                self.menu.insert_command(
                    4, label="彻底删除此对话", foreground="red",
                    command=self.purge_session)
                self._has_delete = True
        else:
            self.menu.entryconfigure(1, label="移到回收站", command=self.recycle)''',
'''        if self.mode == "recycle":
            self.menu.entryconfigure(1, label=self.t("menu_restore"),
                                     command=self.restore_session)
            if not self._has_delete:
                self.menu.insert_command(
                    4, label=self.t("menu_purge"), foreground="red",
                    command=self.purge_session)
                self._has_delete = True
        else:
            self.menu.entryconfigure(1, label=self.t("menu_recycle"),
                                     command=self.recycle)''')

# ---------- 6. 状态栏 ----------
rep('''        prefix = "回收站 · " if self.mode == "recycle" else ""
        self.status.config(text=f"{prefix}共 {len(self.data)} 条, 筛出 {len(self.shown)} 条")''',
'''        prefix = self.t("recycled_prefix") if self.mode == "recycle" else ""
        self.status.config(text=prefix + self.t(
            "status", total=len(self.data), shown=len(self.shown)))''')

# ---------- 7. 文案替换 ----------
rep('''            messagebox.showerror("打开失败", "会话 ID 看起来不对, 不敢拼进命令里。")''',
'''            messagebox.showerror(self.t("err_open"), self.t("err_badid"))''')
rep('''            messagebox.showerror("打开失败", str(e))''',
'''            messagebox.showerror(self.t("err_open"), str(e))''')
rep('''            messagebox.showinfo("提示", "先选中要处理的对话(可按住 Ctrl 多选)。")''',
'''            messagebox.showinfo(self.t("settings"), self.t("hint_select"))''')
rep('''        more = f" 等 {len(items)} 条" if len(items) > 1 else ""
        if not messagebox.askyesno(
                "移到回收站",
                f"确定把「{preview}」{more} 移到回收站?\\n\\n"
                "文件将不会被彻底删除, 将会移动到回收站文件夹, 以后可以恢复。\\n\\n"
                f"回收站位置: {PROJECTS_ROOT / RECYCLE_NAME}"):''',
'''        more = self.t("more", n=len(items)) if len(items) > 1 else ""
        if not messagebox.askyesno(
                self.t("recycle_title"),
                self.t("recycle_msg", preview=preview, more=more,
                       path=PROJECTS_ROOT / RECYCLE_NAME)):''')
rep('''                messagebox.showerror("搬移失败", f"{s['path'].name}\\n{e}")''',
'''                messagebox.showerror(self.t("err_move"), s["path"].name + chr(10) + str(e))''')
rep('''            self.mode_btn.configure(text="打开会话列表")''',
'''            self.mode_btn.configure(text=self.t("open_list"))''')
rep('''            self.mode_btn.configure(text="打开回收站")''',
'''            self.mode_btn.configure(text=self.t("open_recycle"))''')
rep('''                messagebox.showerror("恢复失败", s["path"].name + chr(10) + str(e))''',
'''                messagebox.showerror(self.t("err_restore"), s["path"].name + chr(10) + str(e))''')
rep('''        more = f" 等 {len(items)} 条" if len(items) > 1 else ""
        if not messagebox.askyesno(
                "彻底删除",
                f"您是否要删除「{preview}」{more}?" + chr(10) + chr(10) +
                "这将会使此对话从你的磁盘中永久删除,是否确认?",
                icon="warning"):''',
'''        more = self.t("more", n=len(items)) if len(items) > 1 else ""
        if not messagebox.askyesno(
                self.t("purge_title"),
                self.t("purge_msg", preview=preview, more=more),
                icon="warning"):''')
rep('''                messagebox.showerror("删除失败", s["path"].name + chr(10) + str(e))''',
'''                messagebox.showerror(self.t("err_delete"), s["path"].name + chr(10) + str(e))''')

# ---------- 8. 详情窗口 ----------
rep('''        win.title("对话详情")''', '''        win.title(self.t("detail_title"))''')
rep('''        rows = [
            ("标题", s["title"]),
            ("首句", s["first"] or "(无)"),
            ("项目", s["cwd"] or project_label(s["project"])),
            ("时间", s["mtime"].strftime("%Y-%m-%d %H:%M:%S")),
            ("消息数", str(s["count"])),
            ("大小", human_size(s["size"])),
            ("路径", str(s["path"])),
            ("会话 ID", s["sid"]),
        ]''',
'''        rows = [
            (self.t("d_title"), s["title"]),
            (self.t("d_first"), s["first"] or self.t("d_none")),
            (self.t("d_project"), s["cwd"] or project_label(s["project"])),
            (self.t("d_time"), s["mtime"].strftime("%Y-%m-%d %H:%M:%S")),
            (self.t("d_count"), str(s["count"])),
            (self.t("d_size"), human_size(s["size"])),
            (self.t("d_path"), str(s["path"])),
            (self.t("d_sid"), s["sid"]),
        ]''')
rep('''        ttk.Button(body, text="关闭", command=win.destroy).grid(''',
'''        ttk.Button(body, text=self.t("close"), command=win.destroy).grid(''')

# ---------- 9. 语言 / 配置方法 ----------
rep('''    def open_session(self):''',
'''    def t(self, key, **kw):
        text = TR.get(self.lang, TR["zh"]).get(key, key)
        if kw:
            text = text.format(**kw)
        return text.replace("{nl}", chr(10))

    def open_settings(self):
        if self._settings_win and self._settings_win.winfo_exists():
            self._settings_win.lift()
            return
        win = self._settings_win = tk.Toplevel(self.root)
        win.title(self.t("settings"))
        win.transient(self.root)
        win.geometry("480x190")
        win.resizable(False, False)
        body = ttk.Frame(win, padding=14)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text=self.t("language")).grid(row=0, column=0, sticky="w")
        combo = ttk.Combobox(body, values=["中文", "English"],
                             state="readonly", width=14)
        combo.set("English" if self.lang == "en" else "中文")
        combo.grid(row=0, column=1, sticky="w", padx=(10, 0))
        combo.bind("<<ComboboxSelected>>",
                   lambda e: self.set_language("en" if combo.get() == "English" else "zh"))
        ttk.Button(body, text=self.t("open_memory"),
                   command=self.open_memory).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(16, 0))
        ttk.Button(body, text=self.t("close"), command=win.destroy).grid(
            row=2, column=1, sticky="e", pady=(16, 0))
        body.columnconfigure(1, weight=1)

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
        self.mode_btn.configure(text=self.t("open_recycle")
                                if self.mode == "active" else self.t("open_list"))
        for c, key in (("time", "col_time"), ("title", "col_title"),
                       ("project", "col_project"), ("count", "col_count"),
                       ("size", "col_size")):
            self.tree.heading(c, text=self.t(key))
        self.menu.entryconfigure(0, label=self.t("menu_open"))
        self.menu.entryconfigure(1, label=self.t("menu_restore")
                                 if self.mode == "recycle" else self.t("menu_recycle"))
        self.menu.entryconfigure(2, label=self.t("menu_folder"))
        self.menu.entryconfigure(self.menu.index("end"), label=self.t("menu_detail"))
        self.refresh_view()
        if self._settings_win and self._settings_win.winfo_exists():
            self._settings_win.destroy()
            self.open_settings()

    def open_memory(self):
        if MEMORY_PATH.exists():
            os.startfile(str(MEMORY_PATH))
        else:
            messagebox.showinfo(self.t("settings"),
                                self.t("memory_missing") + ": " + str(MEMORY_PATH))

    def open_session(self):''')

p.write_text(s, encoding="utf-8")
ast.parse(s)
print("patched ok")

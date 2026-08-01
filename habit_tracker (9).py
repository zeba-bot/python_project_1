import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
from datetime import date, timedelta, datetime

DATA_FILE = "habits_data.json"
POINTS = {"Easy": 5, "Medium": 10, "Hard": 20}

# ── Colors ────────────────────────────────────────────────
BG         = "#0d1117"
BG2        = "#161b22"
BG3        = "#21262d"
CARD       = "#1c2128"
BORDER     = "#30363d"
PRIMARY    = "#7c6aff"
PRIMARY_DK = "#6355e0"
GREEN      = "#3fb950"
GREEN_DK   = "#2ea043"
RED        = "#f85149"
GOLD       = "#e3b341"
TEAL       = "#39d0b4"
WHITE      = "#e6edf3"
GRAY       = "#8b949e"
GRAY2      = "#484f58"

EASY_BG = "#0d2b1a"; EASY_FG = "#3fb950"
MED_BG  = "#2b1f00"; MED_FG  = "#e3b341"
HARD_BG = "#2d0f0f"; HARD_FG = "#f85149"

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

DEADLINE_OPTIONS = [
    "No deadline",
    "08:00 AM", "09:00 AM", "10:00 AM", "11:00 AM", "12:00 PM",
    "01:00 PM", "02:00 PM", "03:00 PM", "04:00 PM", "05:00 PM",
    "06:00 PM", "07:00 PM", "08:00 PM", "09:00 PM", "10:00 PM",
]

_notified = set()


# ── Data ──────────────────────────────────────────────────
def load():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            d = json.load(f)
        for key, val in [("day_log", {}), ("streak", 0),
                         ("best_streak", 0), ("default_habits", [])]:
            if key not in d:
                d[key] = val
        return d
    return {"habits": [], "total_points": 0,
            "day_log": {}, "streak": 0, "best_streak": 0,
            "default_habits": []}


def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def sync_default_habits(data):
    today      = date.today().isoformat()
    today_date = date.fromisoformat(today)
    existing   = {h["name"] for h in data["habits"]}
    for dh in data["default_habits"]:
        if dh["duration"] == "70_days":
            start = date.fromisoformat(dh["start_date"])
            if (today_date - start).days >= 70:
                dh["expired"] = True
                continue
        dh["expired"] = False
        if dh["name"] not in existing:
            data["habits"].append({
                "name": dh["name"], "diff": dh["diff"],
                "done_date": None, "is_default": True,
            })


def get_week_dates():
    today  = date.today()
    monday = today - timedelta(days=today.weekday())
    return [(monday + timedelta(days=i)).isoformat() for i in range(7)]


# ── Week Strip ────────────────────────────────────────────
class DayTracker(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=BG2, **kw)
        self._cells = {}
        self._build()

    def _build(self):
        tk.Label(self, text="THIS WEEK", font=("Courier", 9, "bold"),
                 bg=BG2, fg=GRAY).pack(anchor="w", padx=10, pady=(10, 4))

        grid       = tk.Frame(self, bg=BG2)
        grid.pack(fill="x", padx=8, pady=(0, 8))
        week_dates = get_week_dates()
        today_str  = date.today().isoformat()

        for col, (day_name, d_str) in enumerate(zip(DAYS, week_dates)):
            is_today = d_str == today_str
            cell_bg  = "#1c2a3a" if is_today else BG3
            cell = tk.Frame(grid, bg=cell_bg, padx=4, pady=6,
                            highlightthickness=1,
                            highlightbackground=PRIMARY if is_today else BORDER)
            cell.grid(row=0, column=col, padx=2, sticky="nsew")
            grid.columnconfigure(col, weight=1)
            tk.Label(cell, text=day_name, font=("Courier", 8, "bold"),
                     bg=cell_bg, fg=PRIMARY if is_today else GRAY).pack()
            dot = tk.Label(cell, text="●", font=("Segoe UI", 10),
                           bg=cell_bg, fg=GRAY2)
            dot.pack()
            pct = tk.Label(cell, text="–", font=("Courier", 8),
                           bg=cell_bg, fg=GRAY2)
            pct.pack()
            self._cells[d_str] = (cell, pct, dot, cell_bg, is_today)

        streak_row = tk.Frame(self, bg=BG2)
        streak_row.pack(fill="x", padx=10, pady=(0, 10))
        self.streak_lbl = tk.Label(streak_row, text="🔥 Streak: 0 days",
                                    font=("Courier", 9, "bold"), bg=BG2, fg=GOLD)
        self.streak_lbl.pack(side="left")
        self.best_lbl = tk.Label(streak_row, text="Best: 0",
                                  font=("Courier", 9), bg=BG2, fg=GRAY)
        self.best_lbl.pack(side="right")

    def update(self, data):
        habits   = data["habits"]
        day_log  = data.get("day_log", {})
        n_habits = len(habits)
        for d_str, (cell, pct_lbl, dot, cell_bg, is_today) in self._cells.items():
            if n_habits == 0:
                pct_lbl.config(text="–", fg=GRAY2)
                dot.config(fg=GRAY2, text="●")
                continue
            done_count = sum(1 for h in habits if h.get("done_date") == d_str)
            if d_str in day_log:
                done_count = max(done_count, day_log[d_str].get("done", 0))
            pct = int(done_count / n_habits * 100)
            if pct == 100:
                dot.config(fg=GREEN, text="✔")
                pct_lbl.config(text="100%", fg=GREEN)
            elif pct > 0:
                dot.config(fg=GOLD, text="◑")
                pct_lbl.config(text=f"{pct}%", fg=GOLD)
            else:
                dot.config(fg=GRAY2, text="●")
                pct_lbl.config(text="0%", fg=GRAY2)
        streak = data.get("streak", 0)
        best   = data.get("best_streak", 0)
        self.streak_lbl.config(
            text=f"🔥 Streak: {streak} day{'s' if streak != 1 else ''}")
        self.best_lbl.config(text=f"Best: {best}")


# ── Progress Bar Chart ────────────────────────────────────
class ProgressGraph(tk.Canvas):
    """Bar chart: last 14 days, each bar = % habits completed that day."""
    DAYS_SHOWN = 14

    def __init__(self, parent, **kw):
        kw.setdefault("bg", BG2)
        kw.setdefault("highlightthickness", 0)
        super().__init__(parent, **kw)
        self._habits = []
        self._log    = {}
        self._viewed = str(date.today())
        self.bind("<Configure>", lambda e: self._draw())

    def update_data(self, data, viewed_date):
        self._habits = list(data.get("habits", []))
        self._log    = dict(data.get("day_log", {}))
        self._viewed = viewed_date
        self._draw()

    def _draw(self):
        self.delete("all")
        W = self.winfo_width()
        H = self.winfo_height()
        if W < 30 or H < 30:
            return

        n = self.DAYS_SHOWN
        today = date.today()

        pad_l, pad_r, pad_t, pad_b = 36, 10, 12, 28
        plot_w = W - pad_l - pad_r
        plot_h = H - pad_t - pad_b
        gap    = 4
        bar_w  = max(6, (plot_w - gap * (n - 1)) // n)

        # grid lines + y-axis labels
        for pct in [0, 25, 50, 75, 100]:
            y = pad_t + plot_h - int(plot_h * pct / 100)
            self.create_line(pad_l, y, W - pad_r, y,
                             fill=BORDER, dash=(2, 4), width=1)
            self.create_text(pad_l - 4, y, text=f"{pct}%",
                             font=("Courier", 7), fill=GRAY, anchor="e")

        for i in range(n):
            d     = today - timedelta(days=n - 1 - i)
            d_str = d.isoformat()
            n_h   = len(self._habits)

            if n_h == 0:
                completion = 0.0
            else:
                done_live = sum(
                    1 for hb in self._habits if hb.get("done_date") == d_str)
                done_log  = self._log.get(d_str, {}).get("done", 0)
                done      = max(done_live, done_log)
                total     = max(n_h, self._log.get(d_str, {}).get("total", n_h))
                completion = done / total if total else 0.0

            bar_h    = max(3, int(plot_h * completion))
            x0       = pad_l + i * (bar_w + gap)
            x1       = x0 + bar_w
            y_bot    = pad_t + plot_h
            y_top    = y_bot - bar_h

            is_today  = d_str == str(today)
            is_viewed = d_str == self._viewed

            if completion >= 1.0:
                color = GREEN
            elif completion > 0:
                color = GOLD
            else:
                color = BG3

            if is_today:
                color = TEAL
            elif is_viewed:
                color = PRIMARY

            # bar
            self.create_rectangle(x0, y_top, x1, y_bot,
                                   fill=color, outline="")
            # highlight ring
            if is_today or is_viewed:
                self.create_rectangle(x0 - 1, y_top - 1, x1 + 1, y_bot + 1,
                                       outline=color, fill="", width=2)

            # % label on top of bar if > 0
            if completion > 0:
                self.create_text(
                    x0 + bar_w // 2, y_top - 3,
                    text=f"{int(completion*100)}%",
                    font=("Courier", 6), fill=color, anchor="s")

            # x-axis date label
            if i == 0 or i == n - 1 or d.day == 1 or i % 3 == 0:
                try:
                    lbl = d.strftime("%-d")
                except ValueError:
                    lbl = str(d.day)
                self.create_text(
                    x0 + bar_w // 2, H - pad_b + 6,
                    text=lbl, font=("Courier", 7),
                    fill=TEAL if is_today else (PRIMARY if is_viewed else GRAY2),
                    anchor="n")

        # month label bottom-right
        self.create_text(
            W - pad_r, H - 4,
            text=today.strftime("%b %Y"),
            font=("Courier", 7), fill=GRAY2, anchor="se")


# ── Default Habits Manager ────────────────────────────────
class DefaultHabitsManager(tk.Toplevel):
    def __init__(self, parent, data, on_close):
        super().__init__(parent)
        self.data     = data
        self.on_close = on_close
        self.title("Default Habits")
        self.geometry("530x560")
        self.minsize(470, 460)
        self.configure(bg=BG)
        self.resizable(True, True)
        self.grab_set()
        self._build()
        self._refresh_list()

    def _build(self):
        hdr = tk.Frame(self, bg=BG2, pady=12, padx=16)
        hdr.pack(fill="x")
        tk.Label(hdr, text="📌  Default Habits", font=("Georgia", 15, "bold"),
                 bg=BG2, fg=WHITE).pack(side="left")
        tk.Label(hdr, text="Auto-added every day", font=("Courier", 9),
                 bg=BG2, fg=GRAY).pack(side="right", pady=(4, 0))

        form = tk.Frame(self, bg=BG3, padx=14, pady=12)
        form.pack(fill="x", padx=14, pady=(12, 0))
        tk.Label(form, text="NEW DEFAULT HABIT", font=("Courier", 9, "bold"),
                 bg=BG3, fg=TEAL).pack(anchor="w", pady=(0, 8))

        name_row = tk.Frame(form, bg=BG3)
        name_row.pack(fill="x", pady=(0, 6))
        tk.Label(name_row, text="Name:", font=("Courier", 9),
                 bg=BG3, fg=GRAY, width=9, anchor="w").pack(side="left")
        self.dname_var = tk.StringVar()
        e = tk.Entry(name_row, textvariable=self.dname_var,
                     font=("Segoe UI", 10), relief="flat",
                     bg=BG2, fg=WHITE, insertbackground=TEAL,
                     highlightthickness=1, highlightcolor=TEAL,
                     highlightbackground=BORDER)
        e.pack(side="left", fill="x", expand=True, ipady=5)
        e.bind("<Return>", lambda _: self._add_default())

        opts_row = tk.Frame(form, bg=BG3)
        opts_row.pack(fill="x", pady=(0, 6))
        tk.Label(opts_row, text="Difficulty:", font=("Courier", 9),
                 bg=BG3, fg=GRAY, width=9, anchor="w").pack(side="left")
        self.ddiff_var = tk.StringVar(value="Medium (10 pts)")
        ttk.Combobox(opts_row, textvariable=self.ddiff_var,
                     values=["Easy (5 pts)", "Medium (10 pts)", "Hard (20 pts)"],
                     state="readonly", font=("Segoe UI", 9),
                     width=14).pack(side="left", padx=(0, 12))
        tk.Label(opts_row, text="Keep for:", font=("Courier", 9),
                 bg=BG3, fg=GRAY).pack(side="left")
        self.dur_var = tk.StringVar(value="70 Days")
        ttk.Combobox(opts_row, textvariable=self.dur_var,
                     values=["70 Days", "Until Changed"],
                     state="readonly", font=("Segoe UI", 9),
                     width=13).pack(side="left", padx=(4, 0))

        tk.Button(form, text="+ Add Default", font=("Courier", 10, "bold"),
                  bg=TEAL, fg=BG, relief="flat", cursor="hand2",
                  activebackground="#2eb89a", activeforeground=BG,
                  command=self._add_default, padx=12, pady=4).pack(
                      anchor="e", pady=(8, 0))

        tk.Label(self, text="ACTIVE DEFAULT HABITS", font=("Courier", 9, "bold"),
                 bg=BG, fg=GRAY).pack(anchor="w", padx=16, pady=(14, 4))

        cont = tk.Frame(self, bg=BG)
        cont.pack(fill="both", expand=True, padx=14, pady=(0, 10))
        self.list_canvas = tk.Canvas(cont, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(cont, orient="vertical",
                           command=self.list_canvas.yview)
        self.list_frame = tk.Frame(self.list_canvas, bg=BG)
        self.list_frame.bind(
            "<Configure>",
            lambda e: self.list_canvas.configure(
                scrollregion=self.list_canvas.bbox("all")))
        win = self.list_canvas.create_window(
            (0, 0), window=self.list_frame, anchor="nw")
        self.list_canvas.bind(
            "<Configure>",
            lambda e: self.list_canvas.itemconfig(win, width=e.width))
        self.list_canvas.configure(yscrollcommand=sb.set)
        self.list_canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        tk.Button(self, text="✓ Done", font=("Courier", 10, "bold"),
                  bg=PRIMARY, fg=WHITE, relief="flat", cursor="hand2",
                  activebackground=PRIMARY_DK, activeforeground=WHITE,
                  command=self._close, padx=16, pady=5).pack(pady=(0, 12))

    def _add_default(self):
        name = self.dname_var.get().strip()
        if not name:
            messagebox.showwarning("Empty", "Please enter a habit name.",
                                   parent=self)
            return
        if any(dh["name"] == name for dh in self.data["default_habits"]):
            messagebox.showwarning(
                "Duplicate", f"'{name}' is already a default habit.",
                parent=self)
            return
        diff     = self.ddiff_var.get().split(" ")[0]
        duration = ("70_days" if self.dur_var.get() == "70 Days"
                    else "forever")
        self.data["default_habits"].append({
            "name": name, "diff": diff, "duration": duration,
            "start_date": date.today().isoformat(), "expired": False,
        })
        if name not in {h["name"] for h in self.data["habits"]}:
            self.data["habits"].append({
                "name": name, "diff": diff,
                "done_date": None, "is_default": True,
            })
        self.dname_var.set("")
        save(self.data)
        self._refresh_list()

    def _remove_default(self, idx):
        dh  = self.data["default_habits"][idx]
        msg = (f"Remove '{dh['name']}' from defaults?\n"
               f"It will no longer auto-appear in your daily list.")
        if not messagebox.askyesno("Remove Default", msg, parent=self):
            return
        self.data["default_habits"].pop(idx)
        self.data["habits"] = [
            h for h in self.data["habits"]
            if not (h.get("name") == dh["name"] and h.get("is_default"))
        ]
        save(self.data)
        self._refresh_list()

    def _refresh_list(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
        defaults = self.data["default_habits"]
        if not defaults:
            tk.Label(self.list_frame,
                     text="No default habits yet.\nAdd one above 📌",
                     font=("Courier", 10), bg=BG, fg=GRAY,
                     justify="center").pack(pady=24)
            return
        today = date.today()
        for i, dh in enumerate(defaults):
            is_exp  = dh.get("expired", False)
            card_bg = "#161616" if is_exp else CARD
            card    = tk.Frame(self.list_frame, bg=card_bg, pady=9, padx=12)
            card.pack(fill="x", pady=3)
            tk.Frame(card, bg=GRAY2 if is_exp else TEAL,
                     width=3).pack(side="left", fill="y", padx=(0, 10))
            info = tk.Frame(card, bg=card_bg)
            info.pack(side="left", fill="both", expand=True)
            tk.Label(info, text=dh["name"], font=("Segoe UI", 10, "bold"),
                     bg=card_bg, fg=GRAY if is_exp else WHITE,
                     anchor="w").pack(anchor="w")
            if is_exp:
                sub, sub_fg = "Expired · 70 days completed ✓", GRAY
            elif dh["duration"] == "70_days":
                start     = date.fromisoformat(dh["start_date"])
                days_left = max(0, 70 - (today - start).days)
                sub    = f"70-day · {days_left}d left"
                sub_fg = RED if days_left <= 10 else GOLD
            else:
                sub, sub_fg = "Active until changed  ∞", TEAL
            tk.Label(info, text=sub, font=("Courier", 8),
                     bg=card_bg, fg=sub_fg, anchor="w").pack(anchor="w")
            d   = dh["diff"]
            cbg = EASY_BG if d == "Easy" else MED_BG if d == "Medium" else HARD_BG
            cfg = EASY_FG if d == "Easy" else MED_FG if d == "Medium" else HARD_FG
            tk.Label(card, text=f"{d} · {POINTS[d]}pts",
                     font=("Courier", 8, "bold"), bg=cbg, fg=cfg,
                     padx=6, pady=2).pack(side="right", padx=(6, 6))
            tk.Button(card, text="✕", font=("Courier", 10),
                      bg=card_bg, fg=GRAY2, relief="flat", cursor="hand2",
                      activebackground=card_bg, activeforeground=RED,
                      command=lambda idx=i: self._remove_default(idx)
                      ).pack(side="right")

    def _close(self):
        self.on_close()
        self.destroy()


# ── Main App ──────────────────────────────────────────────
class HabitApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Habit Tracker")
        self.geometry("860x750")
        self.minsize(700, 600)
        self.configure(bg=BG)
        self.resizable(True, True)

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TCombobox",
                         fieldbackground=BG3, background=BG3,
                         foreground=WHITE, selectbackground=PRIMARY,
                         bordercolor=BORDER, darkcolor=BG3,
                         lightcolor=BG3, arrowcolor=GRAY)
        style.configure("Vertical.TScrollbar",
                         background=BG3, troughcolor=BG2,
                         bordercolor=BORDER, arrowcolor=GRAY)
        style.map("TCombobox", fieldbackground=[("readonly", BG3)])

        self.data        = load()
        self.today       = str(date.today())
        self.viewed_date = self.today
        sync_default_habits(self.data)
        save(self.data)
        self._build_ui()
        self.refresh()
        self._check_deadlines()
        self._auto_refresh()

    # ── Build UI ──────────────────────────────────────────
    def _build_ui(self):
        # ── Header ──
        hdr = tk.Frame(self, bg=BG2, pady=12, padx=20)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🌿  Habit Tracker",
                 font=("Georgia", 18, "bold"), bg=BG2, fg=WHITE).pack(
                     side="left")
        pts_frame = tk.Frame(hdr, bg="#1f2a14", padx=10, pady=5)
        pts_frame.pack(side="right")
        tk.Label(pts_frame, text="⭐", font=("Segoe UI", 12),
                 bg="#1f2a14", fg=GOLD).pack(side="left")
        self.pts_label = tk.Label(pts_frame, text="0 pts",
                                   font=("Courier", 12, "bold"),
                                   bg="#1f2a14", fg=GOLD)
        self.pts_label.pack(side="left", padx=(4, 0))
        tk.Button(hdr, text="📌 Default Habits",
                  font=("Courier", 9, "bold"),
                  bg=BG3, fg=TEAL, relief="flat", cursor="hand2",
                  activebackground=BORDER, activeforeground=TEAL,
                  padx=10, pady=4,
                  command=self.open_default_manager).pack(
                      side="right", padx=(0, 10))

        # ── Two-column body ──
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)

        # LEFT column — scrollable habits list
        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="both", expand=True)

        # RIGHT column — progress chart
        right = tk.Frame(body, bg=BG2, width=240)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        # ── RIGHT: Progress chart ──
        tk.Label(right, text="PROGRESS CHART",
                 font=("Courier", 9, "bold"), bg=BG2, fg=GRAY).pack(
                     anchor="w", padx=10, pady=(14, 2))
        tk.Label(right,
                 text="% of habits completed each day",
                 font=("Courier", 7), bg=BG2, fg=GRAY2).pack(
                     anchor="w", padx=10)
        self.progress_graph = ProgressGraph(right)
        self.progress_graph.pack(fill="both", expand=True,
                                  padx=8, pady=(6, 12))

        # ── LEFT: Week strip ──
        self.day_tracker = DayTracker(left)
        self.day_tracker.pack(fill="x", padx=12, pady=(8, 4))

        # ── LEFT: Nav bar ──
        nav = tk.Frame(left, bg=BG3, pady=5, padx=12)
        nav.pack(fill="x", padx=12, pady=(0, 4))
        tk.Button(nav, text="◀", font=("Courier", 11, "bold"),
                  bg=BG3, fg=PRIMARY, relief="flat", cursor="hand2",
                  activebackground=BG3, activeforeground=PRIMARY_DK,
                  command=self._prev_day).pack(side="left")
        self.nav_date_label = tk.Label(nav, text="",
                                        font=("Courier", 10, "bold"),
                                        bg=BG3, fg=WHITE)
        self.nav_date_label.pack(side="left", expand=True)
        self.nav_today_btn = tk.Button(
            nav, text="Today", font=("Courier", 9),
            bg=PRIMARY, fg=WHITE, relief="flat", cursor="hand2",
            activebackground=PRIMARY_DK, activeforeground=WHITE,
            padx=8, pady=2, command=self._go_today)
        self.nav_today_btn.pack(side="left", padx=(6, 4))
        tk.Button(nav, text="▶", font=("Courier", 11, "bold"),
                  bg=BG3, fg=PRIMARY, relief="flat", cursor="hand2",
                  activebackground=BG3, activeforeground=PRIMARY_DK,
                  command=self._next_day).pack(side="right")

        # ── LEFT: Stats row ──
        stats = tk.Frame(left, bg=BG, padx=12, pady=4)
        stats.pack(fill="x")
        self.stat_total = self._stat_card(stats, "0", "Habits")
        self.stat_done  = self._stat_card(stats, "0", "Done Today")
        self.stat_today = self._stat_card(stats, "0", "Today's pts")

        # ── LEFT: Add-habit form ──
        add_f = tk.Frame(left, bg=BG3, padx=12, pady=10)
        add_f.pack(fill="x", padx=12, pady=(4, 6))
        tk.Label(add_f, text="NEW HABIT", font=("Courier", 9, "bold"),
                 bg=BG3, fg=PRIMARY).pack(anchor="w", pady=(0, 5))

        r1 = tk.Frame(add_f, bg=BG3)
        r1.pack(fill="x", pady=(0, 5))
        self.name_var = tk.StringVar()
        entry = tk.Entry(r1, textvariable=self.name_var,
                         font=("Segoe UI", 11), relief="flat",
                         bg=BG2, fg=WHITE, insertbackground=PRIMARY,
                         highlightthickness=1, highlightcolor=PRIMARY,
                         highlightbackground=BORDER)
        entry.pack(side="left", fill="x", expand=True, ipady=6)
        entry.bind("<Return>", lambda _: self.add_habit())
        tk.Button(r1, text="+ Add", font=("Courier", 10, "bold"),
                  bg=PRIMARY, fg=WHITE, relief="flat", cursor="hand2",
                  activebackground=PRIMARY_DK, activeforeground=WHITE,
                  command=self.add_habit, padx=12, pady=4).pack(
                      side="left", padx=(8, 0))

        r2 = tk.Frame(add_f, bg=BG3)
        r2.pack(fill="x")
        self.diff_var = tk.StringVar(value="Medium (10 pts)")
        ttk.Combobox(r2, textvariable=self.diff_var,
                     values=["Easy (5 pts)", "Medium (10 pts)", "Hard (20 pts)"],
                     state="readonly", font=("Segoe UI", 10),
                     width=16).pack(side="left")

        r3 = tk.Frame(add_f, bg=BG3)
        r3.pack(fill="x", pady=(5, 0))
        tk.Label(r3, text="⏰ Deadline:", font=("Courier", 9),
                 bg=BG3, fg=GRAY).pack(side="left", padx=(0, 6))
        self.deadline_var = tk.StringVar(value="No deadline")
        ttk.Combobox(r3, textvariable=self.deadline_var,
                     values=DEADLINE_OPTIONS, state="readonly",
                     font=("Segoe UI", 10), width=13).pack(side="left")

        # ── LEFT: Habit list label ──
        self.habit_list_label = tk.Label(
            left, text="TODAY'S HABITS",
            font=("Courier", 9, "bold"), bg=BG, fg=GRAY)
        self.habit_list_label.pack(anchor="w", padx=14, pady=(4, 2))

        # ── LEFT: Scrollable habit list ──
        # Use a plain Frame — NO Canvas wrapper.
        # This is the fix: avoid the Canvas-window width issue entirely.
        outer = tk.Frame(left, bg=BG)
        outer.pack(fill="both", expand=True, padx=12, pady=(0, 4))

        self._list_canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient="vertical",
                           command=self._list_canvas.yview)
        self.scroll_frame = tk.Frame(self._list_canvas, bg=BG)

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self._list_canvas.configure(
                scrollregion=self._list_canvas.bbox("all")))

        self._win_id = self._list_canvas.create_window(
            (0, 0), window=self.scroll_frame, anchor="nw")

        # KEY FIX: keep scroll_frame width = canvas width at all times
        self._list_canvas.bind(
            "<Configure>",
            lambda e: self._list_canvas.itemconfig(
                self._win_id, width=e.width))

        self._list_canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._list_canvas.pack(side="left", fill="both", expand=True)

        self._list_canvas.bind_all(
            "<MouseWheel>",
            lambda e: self._list_canvas.yview_scroll(
                int(-1 * (e.delta / 120)), "units"))

        # ── Footer ──
        footer = tk.Frame(left, bg=BG, pady=6, padx=12)
        footer.pack(fill="x")
        tk.Button(footer, text="↺ Reset Today", font=("Courier", 9),
                  bg=BG3, fg=GRAY, relief="flat", cursor="hand2",
                  padx=8, pady=3, command=self.reset_today).pack(side="left")
        tk.Button(footer, text="🗑 Clear All", font=("Courier", 9),
                  bg=BG3, fg=RED, relief="flat", cursor="hand2",
                  padx=8, pady=3, command=self.clear_all).pack(side="right")

    def _stat_card(self, parent, val, label):
        card = tk.Frame(parent, bg=BG3, padx=10, pady=6)
        card.pack(side="left", expand=True, fill="both", padx=3)
        num = tk.Label(card, text=val,
                       font=("Courier", 18, "bold"), bg=BG3, fg=WHITE)
        num.pack()
        tk.Label(card, text=label, font=("Courier", 8),
                 bg=BG3, fg=GRAY).pack()
        return num

    # ── Navigation ────────────────────────────────────────
    def _prev_day(self):
        vd = date.fromisoformat(self.viewed_date)
        self.viewed_date = (vd - timedelta(days=1)).isoformat()
        self.refresh()

    def _next_day(self):
        vd = date.fromisoformat(self.viewed_date)
        if vd < date.today():
            self.viewed_date = (vd + timedelta(days=1)).isoformat()
            self.refresh()

    def _go_today(self):
        self.viewed_date = str(date.today())
        self.refresh()

    # ── Habit CRUD ────────────────────────────────────────
    def add_habit(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Empty", "Enter a habit name.", parent=self)
            return
        diff     = self.diff_var.get().split(" ")[0]
        deadline = self.deadline_var.get()
        if deadline == "No deadline":
            deadline = None
        self.data["habits"].append({
            "name": name, "diff": diff,
            "done_date": None, "deadline": deadline
        })
        self.name_var.set("")
        save(self.data)
        self.refresh()

    def toggle(self, i):
        h = self.data["habits"][i]
        if h["done_date"] == self.viewed_date:
            h["done_date"] = None
            self.data["total_points"] = max(
                0, self.data["total_points"] - POINTS[h["diff"]])
        else:
            h["done_date"] = self.viewed_date
            self.data["total_points"] += POINTS[h["diff"]]
            self._flash(f"+{POINTS[h['diff']]} pts 🎉")
        self._update_streak()
        save(self.data)
        self.refresh()

    def delete_habit(self, i):
        h = self.data["habits"][i]
        if not messagebox.askyesno(
                "Delete", f"Delete '{h['name']}'?", parent=self):
            return
        if h["done_date"] == self.viewed_date:
            self.data["total_points"] = max(
                0, self.data["total_points"] - POINTS[h["diff"]])
        self.data["habits"].pop(i)
        self._update_streak()
        save(self.data)
        self.refresh()

    def reset_today(self):
        if not self.data["habits"]:
            return
        label = ("today" if self.viewed_date == self.today
                 else date.fromisoformat(self.viewed_date).strftime("%b %d"))
        if messagebox.askyesno("Reset", f"Reset {label}'s progress?",
                               parent=self):
            for h in self.data["habits"]:
                if h["done_date"] == self.viewed_date:
                    h["done_date"] = None
            self._update_streak()
            save(self.data)
            self.refresh()

    def clear_all(self):
        if not self.data["habits"]:
            return
        if messagebox.askyesno("Clear All", "Delete ALL habits?", parent=self):
            self.data["habits"] = []
            save(self.data)
            self.refresh()

    def open_default_manager(self):
        DefaultHabitsManager(self, self.data, self.refresh)

    # ── Streak / log ──────────────────────────────────────
    def _update_streak(self):
        habits = self.data["habits"]
        n      = len(habits)
        if n == 0:
            self.data["streak"] = 0
            return
        streak     = 0
        check_date = date.today()
        while True:
            d_str      = check_date.isoformat()
            done_count = sum(1 for h in habits if h.get("done_date") == d_str)
            log_done   = self.data["day_log"].get(d_str, {}).get("done", 0)
            if max(done_count, log_done) >= n:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break
            if streak > 365:
                break
        self.data["streak"] = streak
        if streak > self.data.get("best_streak", 0):
            self.data["best_streak"] = streak
        today_done = sum(
            1 for h in habits if h.get("done_date") == self.today)
        self.data["day_log"][self.today] = {"done": today_done, "total": n}

    # ── Render ────────────────────────────────────────────
    def refresh(self):
        sync_default_habits(self.data)
        save(self.data)

        self.today = str(date.today())
        vd         = self.viewed_date
        habits     = self.data["habits"]
        pts        = self.data["total_points"]
        done       = [h for h in habits if h["done_date"] == vd]
        today_pts  = sum(POINTS[h["diff"]] for h in done)

        vdate    = date.fromisoformat(vd)
        is_today = vd == self.today
        nav_text = (f"📅  {vdate.strftime('%A, %b %d')}  (Today)"
                    if is_today
                    else f"📅  {vdate.strftime('%A, %b %d')}  "
                         f"({(date.fromisoformat(self.today) - vdate).days}d ago)")
        self.nav_date_label.config(text=nav_text)
        self.nav_today_btn.config(
            state="disabled" if is_today else "normal",
            bg=GRAY2 if is_today else PRIMARY)

        self.habit_list_label.config(
            text="TODAY'S HABITS"
            if is_today else f"HABITS — {vdate.strftime('%b %d').upper()}")

        self.pts_label.config(text=f"{pts} pts")
        self.stat_total.config(text=str(len(habits)))
        self.stat_done.config(text=str(len(done)))
        self.stat_today.config(text=str(today_pts))

        self.day_tracker.update(self.data)
        self.progress_graph.update_data(self.data, self.viewed_date)

        # ── Rebuild habit cards ──
        for w in self.scroll_frame.winfo_children():
            w.destroy()

        if not habits:
            tk.Label(self.scroll_frame,
                     text="No habits yet — add one above!",
                     font=("Courier", 11), bg=BG, fg=GRAY,
                     justify="center").pack(pady=40)
            return

        default_habits = [h for h in habits if h.get("is_default")]
        regular_habits = [h for h in habits if not h.get("is_default")]

        if default_habits:
            self._section_header("📌  DEFAULT HABITS", TEAL)
            for h in default_habits:
                self._habit_row(habits.index(h), h)

        if regular_habits:
            self._section_header("✦  MY HABITS", PRIMARY)
            for h in regular_habits:
                self._habit_row(habits.index(h), h)

    def _section_header(self, text, color):
        row = tk.Frame(self.scroll_frame, bg=BG)
        row.pack(fill="x", pady=(8, 2))
        tk.Label(row, text=text, font=("Courier", 9, "bold"),
                 bg=BG, fg=color).pack(side="left", padx=4)
        tk.Frame(row, bg=BORDER, height=1).pack(
            side="left", fill="x", expand=True, padx=(8, 0), pady=6)

    def _habit_row(self, i, h):
        is_done = h["done_date"] == self.viewed_date
        card_bg = "#121c10" if is_done else CARD

        card = tk.Frame(self.scroll_frame, bg=card_bg,
                        pady=10, padx=10)
        card.pack(fill="x", pady=2, padx=2)

        # accent bar
        now = datetime.now()
        dl  = h.get("deadline")
        accent = GREEN if is_done else BORDER
        if dl and not is_done:
            try:
                dl_dt     = datetime.strptime(
                    f"{self.today} {dl}", "%Y-%m-%d %I:%M %p")
                mins_left = (dl_dt - now).total_seconds() / 60
                accent    = RED if mins_left < 0 else (
                    GOLD if mins_left < 60 else BORDER)
            except ValueError:
                pass
        tk.Frame(card, bg=accent, width=3).pack(
            side="left", fill="y", padx=(0, 10))

        # ✓ / ○ toggle button
        tk.Button(
            card,
            text="✓" if is_done else "○",
            font=("Courier", 14, "bold"),
            bg=card_bg, fg=GREEN if is_done else GRAY,
            relief="flat", cursor="hand2",
            activebackground=card_bg, activeforeground=GREEN,
            command=lambda idx=i: self.toggle(idx)
        ).pack(side="left", padx=(0, 8))

        # name + sub-label
        info = tk.Frame(card, bg=card_bg)
        info.pack(side="left", fill="both", expand=True)

        tk.Label(
            info, text=h["name"],
            font=("Segoe UI", 11, "overstrike" if is_done else "normal"),
            bg=card_bg,
            fg=GRAY if is_done else WHITE,
            anchor="w"
        ).pack(anchor="w")

        parts = []
        if h.get("is_default"):
            parts.append("📌 default")
        parts.append("✅ Done" if is_done else "click ○ to complete")
        if dl and not is_done:
            parts.append(f"⏰ {dl}")
        tk.Label(info, text="  ·  ".join(parts),
                 font=("Courier", 8), bg=card_bg, fg=GRAY,
                 anchor="w").pack(anchor="w")

        # difficulty badge
        d   = h["diff"]
        cbg = EASY_BG if d == "Easy" else MED_BG if d == "Medium" else HARD_BG
        cfg = EASY_FG if d == "Easy" else MED_FG if d == "Medium" else HARD_FG
        tk.Label(card, text=f"{d} · {POINTS[d]}pts",
                 font=("Courier", 9, "bold"), bg=cbg, fg=cfg,
                 padx=6, pady=3).pack(side="right", padx=(4, 4))

        # delete button
        tk.Button(card, text="✕", font=("Courier", 11),
                  bg=card_bg, fg=GRAY2, relief="flat", cursor="hand2",
                  activebackground=card_bg, activeforeground=RED,
                  command=lambda idx=i: self.delete_habit(idx)
                  ).pack(side="right")

    # ── Timers ────────────────────────────────────────────
    def _auto_refresh(self):
        self.progress_graph.update_data(self.data, self.viewed_date)
        self.after(60_000, self._auto_refresh)

    def _check_deadlines(self):
        now   = datetime.now()
        today = now.date().isoformat()
        overdue = []
        for h in self.data["habits"]:
            dl = h.get("deadline")
            if not dl or h.get("done_date") == today:
                continue
            key = (h["name"], today)
            if key in _notified:
                continue
            try:
                dl_dt = datetime.strptime(
                    f"{today} {dl}", "%Y-%m-%d %I:%M %p")
            except ValueError:
                continue
            if now >= dl_dt:
                overdue.append(h)
                _notified.add(key)
        if overdue:
            self._show_deadline_alert(overdue)
        self.after(60_000, self._check_deadlines)

    def _show_deadline_alert(self, habits):
        alert = tk.Toplevel(self)
        alert.title("⏰ Deadline Missed!")
        alert.configure(bg=BG)
        alert.attributes("-topmost", True)
        alert.resizable(False, False)
        tk.Frame(alert, bg=RED, height=4).pack(fill="x")
        hdr = tk.Frame(alert, bg=BG2, pady=12, padx=16)
        hdr.pack(fill="x")
        tk.Label(hdr, text="⏰  Deadline Passed!",
                 font=("Georgia", 14, "bold"), bg=BG2, fg=RED).pack(
                     side="left")
        body = tk.Frame(alert, bg=BG, padx=18, pady=12)
        body.pack(fill="x")
        tk.Label(body, text="These habits weren't completed in time:",
                 font=("Courier", 9), bg=BG, fg=GRAY).pack(
                     anchor="w", pady=(0, 8))
        for h in habits:
            row = tk.Frame(body, bg=CARD, padx=10, pady=8)
            row.pack(fill="x", pady=3)
            tk.Frame(row, bg=RED, width=3).pack(
                side="left", fill="y", padx=(0, 10))
            tk.Label(row, text=h["name"],
                     font=("Segoe UI", 11, "bold"), bg=CARD,
                     fg=WHITE, anchor="w").pack(side="left")
            tk.Label(row, text=f"  due {h['deadline']}",
                     font=("Courier", 9), bg=CARD, fg=RED,
                     anchor="w").pack(side="left")
        btn_row = tk.Frame(alert, bg=BG, pady=10, padx=16)
        btn_row.pack(fill="x")
        tk.Button(btn_row, text="✓ Got it",
                  font=("Courier", 10, "bold"),
                  bg=GREEN, fg=BG, relief="flat", cursor="hand2",
                  activebackground=GREEN_DK, activeforeground=BG,
                  padx=14, pady=6,
                  command=alert.destroy).pack(side="left")
        tk.Button(btn_row, text="Dismiss",
                  font=("Courier", 10), bg=BG3, fg=GRAY,
                  relief="flat", cursor="hand2",
                  activebackground=BORDER, activeforeground=WHITE,
                  padx=10, pady=6,
                  command=alert.destroy).pack(side="right")
        self.update_idletasks()
        aw, ah = 400, 240 + len(habits) * 52
        x = self.winfo_x() + (self.winfo_width()  - aw) // 2
        y = self.winfo_y() + (self.winfo_height() - ah) // 2
        alert.geometry(f"{aw}x{ah}+{x}+{y}")

    def _flash(self, msg):
        popup = tk.Toplevel(self)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(bg="#1a2e15")
        tk.Label(popup, text=msg, font=("Courier", 13, "bold"),
                 bg="#1a2e15", fg=GREEN, padx=20, pady=10).pack()
        self.update_idletasks()
        x = self.winfo_x() + self.winfo_width() // 2 - 80
        y = self.winfo_y() + 60
        popup.geometry(f"+{x}+{y}")
        popup.after(1800, popup.destroy)


if __name__ == "__main__":
    app = HabitApp()
    app.mainloop()

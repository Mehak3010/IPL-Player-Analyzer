import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
matplotlib.use('TkAgg')
matplotlib.rcParams['font.family'] = 'Segoe UI Emoji'
matplotlib.rcParams['font.sans-serif'] = ['Segoe UI Emoji', 'Segoe UI Symbol', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False
import numpy as np
import csv
import os
from PIL import Image, ImageTk

# ─────────────────────────────────────────────
#  DATA STORE
# ─────────────────────────────────────────────
players_data = []   # list of dicts: {name, runs, wickets, sr, score}
TOP_N_CHARTS = 20
LEFT_IMAGE_SCALE = 0.9

# ─────────────────────────────────────────────
#  SCORE FORMULA
# ─────────────────────────────────────────────
def calc_score(runs, wickets, sr):
    return runs + (wickets * 20) + sr

# ─────────────────────────────────────────────
#  MAIN APPLICATION CLASS
# ─────────────────────────────────────────────
class IPLAnalyzer:
    def __init__(self, root: tk.Tk):
        self.root = root                                       # Tk() – function 1
        self.root.title("🏏  IPL Player Statistics Analyzer")
        self.root.geometry("900x680")
        self.root.configure(bg="#0d1b2a")
        self.root.resizable(True, True)

        # colour palette
        self.C = {
            "bg":      "#0d1b2a",
            "panel":   "#162032",
            "accent":  "#f5a623",
            "accent2": "#e94560",
            "text":    "#e8eaf6",
            "muted":   "#8892a4",
            "green":   "#00e676",
            "entry":   "#1e2d40",
            "border":  "#253a52",
        }

        self.sort_var = tk.StringVar(value="Performance Score")

        self._build_ui()
        if not self._load_csv("ipl_players.csv"):
            messagebox.showinfo("Missing CSV", "Place 'ipl_players.csv' in the project folder.")
            self._refresh_list()

    # ──────────────────────────────────────────
    #  UI BUILDER
    # ──────────────────────────────────────────
    def _build_ui(self):
        # ── HEADER ───────────────────────────
        hdr = tk.Frame(self.root, bg=self.C["accent2"], pady=10)   # Frame() – function 5
        hdr.pack(fill="x")                                          # pack() – function 10

        tk.Label(hdr,                                               # Label() – function 2
                 text="🏏  IPL PLAYER STATISTICS ANALYZER",
                 font=("Georgia", 20, "bold"),
                 bg=self.C["accent2"], fg="white").pack()

        tk.Label(hdr,
                 text="Performance Score  =  Runs  +  (Wickets × 20)  +  Strike Rate",
                 font=("Courier", 10), bg=self.C["accent2"],
                 fg="#ffe0b2").pack()

        # ── MAIN BODY ────────────────────────
        body = tk.Frame(self.root, bg=self.C["bg"])
        body.pack(fill="both", expand=True, padx=10, pady=8)

        left  = tk.Frame(body, bg=self.C["bg"], width=320)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)

        right = tk.Frame(body, bg=self.C["bg"])
        right.pack(side="left", fill="both", expand=True)

        self._build_input_panel(left)
        self._build_left_image_panel(left)
        self._build_controls(right)
        right_content = tk.Frame(right, bg=self.C["bg"])
        right_content.pack(fill="both", expand=True)
        self._build_list_panel(right_content)
        self._build_chart_panel(right_content)

    # ── INPUT PANEL ──────────────────────────
    def _build_input_panel(self, parent):
        pnl = tk.Frame(parent, bg=self.C["panel"],
                       relief="flat", bd=0, pady=10)
        pnl.pack(pady=(0, 8), anchor="center")

        tk.Label(pnl, text="ADD PLAYER", font=("Georgia", 12, "bold"),
                 bg=self.C["panel"], fg=self.C["accent"]).pack(pady=(0, 8))

        fields = [
            ("Player Name",  "name"),
            ("Runs",         "runs"),
            ("Wickets",      "wickets"),
            ("Strike Rate",  "sr"),
        ]
        self.entries = {}
        for label_text, key in fields:
            row = tk.Frame(pnl, bg=self.C["panel"])
            row.pack(fill="x", padx=12, pady=3)
            tk.Label(row, text=label_text, width=12, anchor="w",   # Label reuse
                     font=("Helvetica", 10), bg=self.C["panel"],
                     fg=self.C["text"]).pack(side="left")
            ent = tk.Entry(row, font=("Courier", 11),              # Entry() – function 3
                           bg=self.C["entry"], fg=self.C["text"],
                           insertbackground=self.C["accent"],
                           relief="flat", bd=4)
            ent.pack(side="left", fill="x", expand=True)
            self.entries[key] = ent

        # search field
        sep = tk.Frame(pnl, bg=self.C["border"], height=1)
        sep.pack(fill="x", padx=12, pady=6)
        tk.Label(pnl, text="SEARCH PLAYER", font=("Helvetica", 10, "bold"),
                 bg=self.C["panel"], fg=self.C["muted"]).pack()
        search_row = tk.Frame(pnl, bg=self.C["panel"])
        search_row.pack(fill="x", padx=12, pady=3)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._filter_list)
        tk.Entry(search_row, textvariable=self.search_var,           # Entry reuse
                 font=("Courier", 10), bg=self.C["entry"],
                 fg=self.C["text"], insertbackground=self.C["accent"],
                 relief="flat", bd=4).pack(fill="x")

        # stat selector (right panel)

        # buttons
        btn_row = tk.Frame(pnl, bg=self.C["panel"])
        btn_row.pack(fill="x", padx=12, pady=(4, 0))
        self._btn(btn_row, "➕  Add Player",    self._add_player,
                  self.C["green"],   "#000").pack(side="left", fill="x",
                                                   expand=True, padx=(0, 4))
        self._btn(btn_row, "🗑  Delete",        self._delete_player,
                  self.C["accent2"], "#fff").pack(side="left", fill="x",
                                                   expand=True)
        self._btn(pnl, "💾  Save to CSV",       self._save_csv,
                  self.C["accent"],  "#000").pack(fill="x", padx=12, pady=(6, 4))
        img_sep = tk.Frame(pnl, bg=self.C["border"], height=1)
        img_sep.pack(fill="x", padx=12, pady=6)

    # ── PLAYER LIST ──────────────────────────
    def _build_list_panel(self, parent):
        pnl = tk.Frame(parent, bg=self.C["panel"], width=300)
        pnl.pack(side="right", fill="y", padx=(8, 0))
        pnl.pack_propagate(False)

        hdr_row = tk.Frame(pnl, bg=self.C["panel"])
        hdr_row.pack(fill="x", pady=(8, 4), padx=8)
        tk.Label(hdr_row, text="PLAYER LIST", font=("Georgia", 11, "bold"),
                 bg=self.C["panel"], fg=self.C["accent"]).pack(side="left")
        tk.Label(hdr_row, text="Sort by:", font=("Helvetica", 9),
                 bg=self.C["panel"], fg=self.C["muted"]).pack(side="left", padx=(10, 4))
        opts = ["Performance Score", "Runs", "Wickets", "Strike Rate"]
        om = tk.OptionMenu(hdr_row, self.sort_var, *opts, command=self._refresh_list)
        om.config(bg=self.C["entry"], fg=self.C["text"], activebackground=self.C["accent"],
                  activeforeground="#000", relief="flat", font=("Helvetica", 9),
                  highlightthickness=0, width=18)
        om["menu"].config(bg=self.C["entry"], fg=self.C["text"], activebackground=self.C["accent"])
        om.pack(side="left", fill="x", expand=True, padx=(4, 8))

        list_frame = tk.Frame(pnl, bg=self.C["panel"])
        list_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        sb = tk.Scrollbar(list_frame, orient="vertical",              # Scrollbar() – function 7
                          bg=self.C["border"], troughcolor=self.C["bg"])
        sb.pack(side="right", fill="y")

        self.listbox = tk.Listbox(list_frame,                         # Listbox() – function 6
                                  font=("Courier", 10),
                                  bg=self.C["entry"], fg=self.C["text"],
                                  selectbackground=self.C["accent"],
                                  selectforeground="#000",
                                  activestyle="none",
                                  relief="flat", bd=0,
                                  yscrollcommand=sb.set,
                                  exportselection=False)
        self.listbox.pack(side="left", fill="both", expand=True)
        sb.config(command=self.listbox.yview)

    # ── CONTROLS ─────────────────────────────
    def _build_controls(self, parent):
        ctrl = tk.Frame(parent, bg=self.C["panel"], pady=8)
        ctrl.pack(fill="x", pady=(0, 8))

        tk.Label(ctrl, text="ANALYSIS TOOLS", font=("Georgia", 11, "bold"),
                 bg=self.C["panel"], fg=self.C["accent"]).pack(pady=(0, 6))

        cmp_row = tk.Frame(ctrl, bg=self.C["panel"])
        cmp_row.pack(fill="x", pady=(0, 6))
        tk.Label(cmp_row, text="Compare:", font=("Helvetica", 10),
                 bg=self.C["panel"], fg=self.C["muted"]).pack(side="left", padx=(0, 6))
        self.compare_p1_var = tk.StringVar()
        self.compare_p2_var = tk.StringVar()
        self.compare_p1_cb = ttk.Combobox(cmp_row, textvariable=self.compare_p1_var,
                                          state="readonly", font=("Courier", 10))
        self.compare_p2_cb = ttk.Combobox(cmp_row, textvariable=self.compare_p2_var,
                                          state="readonly", font=("Courier", 10))
        self.compare_p1_cb.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.compare_p2_cb.pack(side="left", fill="x", expand=True)

        topn_row = tk.Frame(ctrl, bg=self.C["panel"])
        topn_row.pack(fill="x", pady=(0, 6))
        tk.Label(topn_row, text="Top N:", font=("Helvetica", 10),
                 bg=self.C["panel"], fg=self.C["muted"]).pack(side="left", padx=(0, 6))
        self.top_n_var = tk.StringVar(value=str(TOP_N_CHARTS))
        tk.OptionMenu(topn_row, self.top_n_var, "10", "15", "20",
                      command=self._on_topn_change
                     ).pack(side="left")

        viz_row = tk.Frame(ctrl, bg=self.C["panel"])
        viz_row.pack(fill="x", pady=(0, 6))
        tk.Label(viz_row, text="Visualize:", font=("Helvetica", 10),
                 bg=self.C["panel"], fg=self.C["muted"]).pack(side="left", padx=(0, 6))
        self.viz_field_var = tk.StringVar(value="Performance Score")
        for lbl in ["Performance Score", "Runs", "Wickets", "Strike Rate"]:
            tk.Radiobutton(viz_row, text=lbl, variable=self.viz_field_var, value=lbl,
                           bg=self.C["panel"], fg=self.C["text"], selectcolor=self.C["entry"],
                           activebackground=self.C["accent"], activeforeground="#000",
                           font=("Helvetica", 9), highlightthickness=0,
                           command=self._on_viz_change).pack(side="left", padx=6)

        btn_grid = tk.Frame(ctrl, bg=self.C["panel"])              # Frame reuse
        btn_grid.pack()

        btns = [
            ("📊 Runs Bar Chart",        self._chart_runs,    self.C["accent"]),
            ("🕸  Radar Chart",          self._chart_radar,   "#7c4dff"),
            ("🏆 Top Performer",         self._show_top,      self.C["green"]),
            ("📋 Rankings",              self._show_rankings, "#00b8d4"),
            ("📈 Score Comparison",      self._chart_score,   self.C["accent2"]),
            ("👥 Player Comparison",     self._chart_compare, "#ff6d00"),
            ("📊 Selected Field Chart",  self._chart_selected, self.C["accent"]),
        ]
        for i, (txt, cmd, clr) in enumerate(btns):
            self._btn(btn_grid, txt, cmd, clr,
                      "#000" if clr in (self.C["accent"], self.C["green"]) else "#fff",
                      width=18).grid(row=i // 3, column=i % 3,    # grid() – function 10b
                                     padx=4, pady=4)
        self._refresh_compare_selectors()

    def _on_viz_change(self, *_):
        try:
            self._chart_selected()
        except Exception:
            pass

    def _on_topn_change(self, *_):
        self._refresh_list()
        try:
            self._chart_selected()
        except Exception:
            pass

    # ── CHART EMBED AREA ─────────────────────
    def _build_chart_panel(self, parent):
        self.chart_frame = tk.Frame(parent, bg=self.C["bg"])       # Frame reuse
        self.chart_frame.pack(side="left", fill="both", expand=True)
        tk.Label(self.chart_frame, text="Charts will appear here",
                 font=("Helvetica", 12), bg=self.C["bg"],
                 fg=self.C["muted"]).pack(expand=True)
    def _build_left_image_panel(self, parent):
        path = self._find_left_image()
        if not path:
            return
        self.left_img_frame = tk.Frame(parent, bg=self.C["panel"])
        self.left_img_frame.pack(fill="both", expand=True, padx=8, pady=(0, 2))
        self.left_img_label = tk.Label(self.left_img_frame, bg=self.C["panel"])
        self.left_img_label.pack(fill="both", expand=True)
        self._load_left_image(path)
    def _find_left_image(self):
        for cand in ["OpeningImg.png","left_image.png","left_image.jpg","left_image.jpeg","poster.png","poster.jpg"]:
            cand_path = os.path.join(os.getcwd(), cand)
            if os.path.exists(cand_path):
                return cand_path
        return None
    def _load_left_image(self, path):
        try:
            img = Image.open(path)
        except Exception:
            return
        w = 300
        h = 340
        img.thumbnail((int(w * LEFT_IMAGE_SCALE), int(h * LEFT_IMAGE_SCALE)), Image.Resampling.LANCZOS)
        self.left_img_tk = ImageTk.PhotoImage(img)
        self.left_img_label.configure(image=self.left_img_tk)

    # ──────────────────────────────────────────
    #  HELPERS
    # ──────────────────────────────────────────
    def _btn(self, parent, text, cmd, bg, fg="#fff", width=None):
        kw = dict(font=("Helvetica", 9, "bold"), relief="flat",
                  bd=0, padx=8, pady=6, cursor="hand2",
                  activebackground=bg, activeforeground=fg)
        if width:
            kw["width"] = width
        b = tk.Button(parent, text=text, bg=bg, fg=fg,             # Button() – function 4
                      command=cmd, **kw)
        return b

    def _embed_figure(self, fig):
        for w in self.chart_frame.winfo_children():
            w.destroy()
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        plt.close(fig)

    def _sorted_players(self):
        key_map = {
            "Performance Score": "score",
            "Runs":              "runs",
            "Wickets":           "wickets",
            "Strike Rate":       "sr",
        }
        k = key_map.get(self.sort_var.get(), "score")
        return sorted(players_data, key=lambda p: p[k], reverse=True)

    def _refresh_list(self, *_):
        self.listbox.delete(0, "end")
        q = self.search_var.get().lower()
        for p in self._sorted_players():
            if q in p["name"].lower():
                self.listbox.insert("end",
                    f"  {p['name']:<20}  R:{p['runs']:>4}  "
                    f"W:{p['wickets']:>3}  SR:{p['sr']:>6.1f}  "
                    f"Sc:{p['score']:>7.1f}")
        self._refresh_compare_selectors()

    def _filter_list(self, *_):
        self._refresh_list()

    def _get_top_n(self):
        try:
            return int(self.top_n_var.get())
        except Exception:
            return TOP_N_CHARTS

    def _refresh_compare_selectors(self):
        names = [p["name"] for p in self._sorted_players()]
        if hasattr(self, "compare_p1_cb"):
            self.compare_p1_cb["values"] = names
            self.compare_p2_cb["values"] = names
            if len(names) >= 2:
                if not self.compare_p1_var.get() or self.compare_p1_var.get() not in names:
                    self.compare_p1_var.set(names[0])
                if (not self.compare_p2_var.get() or
                    self.compare_p2_var.get() not in names or
                    self.compare_p2_var.get() == self.compare_p1_var.get()):
                    self.compare_p2_var.set(names[1])

    # ──────────────────────────────────────────
    #  ACTIONS
    # ──────────────────────────────────────────
    def _add_player(self):
        name = self.entries["name"].get().strip()
        if not name:
            messagebox.showwarning("Missing", "Player name is required!")  # messagebox – function 8
            return
        try:
            runs  = float(self.entries["runs"].get())
            wkts  = float(self.entries["wickets"].get())
            sr    = float(self.entries["sr"].get())
        except ValueError:
            messagebox.showerror("Invalid", "Runs / Wickets / SR must be numbers.")
            return
        # check duplicate
        if any(p["name"].lower() == name.lower() for p in players_data):
            messagebox.showwarning("Duplicate", f"'{name}' already exists.")
            return
        score = calc_score(runs, wkts, sr)
        players_data.append({"name": name, "runs": runs,
                              "wickets": wkts, "sr": sr, "score": score})
        for e in self.entries.values():
            e.delete(0, "end")
        self._refresh_list()
        messagebox.showinfo("Added", f"✅  {name} added!\nScore: {score:.1f}")

    def _delete_player(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Select", "Select a player to delete.")
            return
        row_text = self.listbox.get(sel[0]).strip()
        pname = row_text.split("R:")[0].strip()
        global players_data
        players_data = [p for p in players_data
                        if p["name"].lower() != pname.lower()]
        self._refresh_list()

    def _save_csv(self):
        if not players_data:
            messagebox.showinfo("Empty", "No data to save.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            title="Save IPL Data")
        if not path:
            return
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["name","runs","wickets","sr","score"])
            w.writeheader()
            w.writerows(players_data)
        messagebox.showinfo("Saved", f"Data saved to:\n{path}")
    def _load_csv(self, path="ipl_players.csv"):
        if not os.path.exists(path):
            return False
        players_data.clear()
        with open(path, "r", newline="", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                name = (row.get("Player") or row.get("Name") or row.get("name") or "").strip()
                if not name:
                    continue
                try:
                    runs = float((row.get("Runs") or "0").strip() or 0)
                    wickets = float((row.get("Wickets") or "0").strip() or 0)
                    sr = float((row.get("StrikeRate") or row.get("Strike Rate") or row.get("SR") or "0").strip() or 0)
                except ValueError:
                    continue
                score = calc_score(runs, wickets, sr)
                players_data.append({"name": name, "runs": runs, "wickets": wickets, "sr": sr, "score": score})
        self._refresh_list()
        return True

    # ──────────────────────────────────────────
    #  CHARTS
    # ──────────────────────────────────────────
    def _chart_runs(self):
        if not players_data:
            messagebox.showinfo("No Data", "Add players first."); return
        sp = self._sorted_players()[:self._get_top_n()]
        names = [p["name"].split()[-1] for p in sp]
        runs  = [p["runs"] for p in sp]

        fig, ax = plt.subplots(figsize=(6, 3.8))
        fig.patch.set_facecolor("#162032")
        ax.set_facecolor("#0d1b2a")
        colors = plt.cm.YlOrRd(np.linspace(0.4, 0.9, len(names)))
        bars = ax.barh(names[::-1], runs[::-1], color=colors[::-1],
                       edgecolor="none", height=0.6)
        max_val = max(runs) if runs else 0
        pad = max(20, max_val * 0.08)
        ax.set_xlim(0, max_val + pad)
        for bar, val in zip(bars, runs[::-1]):
            limit = ax.get_xlim()[1]
            inside = val > (limit - pad * 0.6)
            x = val - 5 if inside else val + 5
            ha = "right" if inside else "left"
            ax.text(x, bar.get_y() + bar.get_height()/2,
                    f"{int(val)}", va="center", ha=ha, color="#f5a623",
                    fontsize=9, fontweight="bold")
        ax.set_xlabel("Runs", color="#8892a4")
        ax.set_title("🏏  Runs Comparison", color="#f5a623",
                     fontsize=13, fontweight="bold", pad=10)
        ax.tick_params(colors="#e8eaf6", labelsize=9)
        ax.spines[:].set_color("#253a52")
        ax.xaxis.label.set_color("#8892a4")
        fig.tight_layout()
        self._embed_figure(fig)

    def _chart_selected(self):
        if not players_data:
            messagebox.showinfo("No Data", "Add players first."); return
        key_map = {
            "Performance Score": ("score", "Performance Score"),
            "Runs":              ("runs",  "Runs"),
            "Wickets":           ("wickets","Wickets"),
            "Strike Rate":       ("sr",    "Strike Rate"),
        }
        k, label = key_map.get(self.viz_field_var.get(), ("score","Performance Score"))
        sp = sorted(players_data, key=lambda p: p[k], reverse=True)[:self._get_top_n()]
        names = [p["name"].split()[-1] for p in sp]
        vals  = [p[k] for p in sp]
        fig, ax = plt.subplots(figsize=(6, 3.8))
        fig.patch.set_facecolor("#162032")
        ax.set_facecolor("#0d1b2a")
        colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(names)))
        bars = ax.barh(names[::-1], vals[::-1], color=colors[::-1],
                       edgecolor="none", height=0.6)
        max_val = max(vals) if vals else 0
        pad = max(20, max_val * 0.08)
        ax.set_xlim(0, max_val + pad)
        ax.set_xlabel(label, color="#8892a4")
        ax.set_title(f"📊  {label} (Selected)", color="#f5a623",
                     fontsize=13, fontweight="bold")
        ax.tick_params(colors="#e8eaf6", labelsize=9)
        ax.spines[:].set_color("#253a52")
        for bar, val in zip(bars, vals[::-1]):
            limit = ax.get_xlim()[1]
            inside = val > (limit - pad * 0.6)
            x = val - 5 if inside else val + 5
            ha = "right" if inside else "left"
            fmt = f"{int(val)}" if label in ("Runs","Wickets") else f"{val:.1f}"
            ax.text(x, bar.get_y() + bar.get_height()/2,
                    fmt, va="center", ha=ha, color="#00e676",
                    fontsize=8, fontweight="bold")
        fig.tight_layout()
        self._embed_figure(fig)
    def _chart_score(self):
        if not players_data:
            messagebox.showinfo("No Data", "Add players first."); return
        sp = self._sorted_players()[:self._get_top_n()]
        names  = [p["name"].split()[-1] for p in sp]
        scores = [p["score"] for p in sp]
        fig, ax = plt.subplots(figsize=(6, 3.8))
        fig.patch.set_facecolor("#162032")
        ax.set_facecolor("#0d1b2a")
        colors = plt.cm.cool(np.linspace(0.3, 0.9, len(names)))
        bars = ax.barh(names[::-1], scores[::-1], color=colors[::-1],
                       edgecolor="none", height=0.6)
        max_val = max(scores) if scores else 0
        pad = max(20, max_val * 0.08)
        ax.set_xlim(0, max_val + pad)
        ax.set_xlabel("Performance Score", color="#8892a4")
        ax.set_title("⚡  Performance Score Comparison",
                     color="#f5a623", fontsize=13, fontweight="bold")
        ax.tick_params(colors="#e8eaf6", labelsize=9)
        ax.spines[:].set_color("#253a52")
        for bar, val in zip(bars, scores[::-1]):
            limit = ax.get_xlim()[1]
            inside = val > (limit - pad * 0.6)
            x = val - 5 if inside else val + 5
            ha = "right" if inside else "left"
            ax.text(x, bar.get_y() + bar.get_height()/2,
                    f"{val:.0f}", va="center", ha=ha, color="#00e676",
                    fontsize=8, fontweight="bold")
        fig.tight_layout()
        self._embed_figure(fig)

    def _chart_radar(self):
        if len(players_data) < 2:
            messagebox.showinfo("Need Data", "Add at least 2 players."); return
        sp = self._sorted_players()[:5]  # top 5
        categories = ["Runs", "Wickets×10", "Strike Rate"]
        N = len(categories)
        angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(5, 4),
                               subplot_kw=dict(polar=True))
        fig.patch.set_facecolor("#162032")
        ax.set_facecolor("#0d1b2a")

        palette = ["#f5a623","#e94560","#00e676","#7c4dff","#00b8d4"]

        # normalise
        all_r  = [p["runs"]    for p in sp]
        all_w  = [p["wickets"] for p in sp]
        all_sr = [p["sr"]      for p in sp]
        mx_r  = max(all_r)  or 1
        mx_w  = max(all_w)  or 1
        mx_sr = max(all_sr) or 1

        patches = []
        for i, p in enumerate(sp):
            vals = [p["runs"]/mx_r,
                    p["wickets"]/mx_w,
                    p["sr"]/mx_sr]
            vals += vals[:1]
            ax.plot(angles, vals, color=palette[i], linewidth=2)
            ax.fill(angles, vals, color=palette[i], alpha=0.18)
            patches.append(mpatches.Patch(color=palette[i],
                                          label=p["name"].split()[-1]))

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, color="#e8eaf6", size=10)
        ax.tick_params(colors="#8892a4")
        ax.set_yticklabels([])
        ax.grid(color="#253a52")
        ax.spines["polar"].set_color("#253a52")
        ax.set_title("🕸  Performance Radar (top 5)",
                     color="#f5a623", fontsize=12,
                     fontweight="bold", pad=14)
        ax.legend(handles=patches, loc="upper right",
                  bbox_to_anchor=(1.35, 1.15),
                  facecolor="#162032", edgecolor="#253a52",
                  labelcolor="#e8eaf6", fontsize=8)
        fig.tight_layout()
        self._embed_figure(fig)

    def _chart_compare(self):
        if len(players_data) < 2:
            messagebox.showinfo("Need Data", "Add at least 2 players."); return
        n1 = self.compare_p1_var.get().strip()
        n2 = self.compare_p2_var.get().strip()
        if not n1 or not n2:
            messagebox.showwarning("Select", "Choose two players to compare."); return
        if n1 == n2:
            messagebox.showwarning("Select", "Choose two different players."); return
        p1 = next((p for p in players_data if p["name"] == n1), None)
        p2 = next((p for p in players_data if p["name"] == n2), None)
        if not p1 or not p2:
            messagebox.showerror("Missing", "Selected players not found."); return
        cats = ["Runs", "Wickets×20", "Strike Rate"]
        v1 = [p1["runs"], p1["wickets"]*20, p1["sr"]]
        v2 = [p2["runs"], p2["wickets"]*20, p2["sr"]]
        x = np.arange(len(cats))
        fig, ax = plt.subplots(figsize=(6, 3.8))
        fig.patch.set_facecolor("#162032")
        ax.set_facecolor("#0d1b2a")
        w = 0.35
        ax.bar(x - w/2, v1, w, label=p1["name"].split()[-1],
               color="#f5a623", edgecolor="none")
        ax.bar(x + w/2, v2, w, label=p2["name"].split()[-1],
               color="#e94560", edgecolor="none")
        ax.set_xticks(x); ax.set_xticklabels(cats, color="#e8eaf6")
        ax.set_title(f"👥  {p1['name'].split()[-1]}  vs  {p2['name'].split()[-1]}",
                     color="#f5a623", fontsize=12, fontweight="bold")
        ax.tick_params(colors="#8892a4")
        ax.spines[:].set_color("#253a52")
        ax.legend(facecolor="#162032", edgecolor="#253a52",
                  labelcolor="#e8eaf6")
        fig.tight_layout()
        self._embed_figure(fig)

    # ──────────────────────────────────────────
    #  INFO POPUPS
    # ──────────────────────────────────────────
    def _show_top(self):
        if not players_data:
            messagebox.showinfo("No Data", "Add players first."); return
        top = max(players_data, key=lambda p: p["score"])
        msg = (f"🏆  TOP PERFORMER\n\n"
               f"  Name        :  {top['name']}\n"
               f"  Runs        :  {int(top['runs'])}\n"
               f"  Wickets     :  {int(top['wickets'])}\n"
               f"  Strike Rate :  {top['sr']:.1f}\n"
               f"  ─────────────────────\n"
               f"  Perf. Score :  {top['score']:.1f}")
        messagebox.showinfo("Top Performer", msg)           # messagebox reuse

    def _show_rankings(self):
        if not players_data:
            messagebox.showinfo("No Data", "Add players first."); return
        sp = self._sorted_players()
        top = tk.Toplevel(self.root)
        top.title("Rankings")
        top.configure(bg=self.C["panel"])
        top.geometry("420x520")
        hdr = tk.Label(top, text="🏅  PLAYER RANKINGS",
                       font=("Georgia", 12, "bold"),
                       bg=self.C["panel"], fg=self.C["accent"])
        hdr.pack(pady=(8, 4))
        frame = tk.Frame(top, bg=self.C["panel"])
        frame.pack(fill="both", expand=True, padx=8, pady=8)
        sb = tk.Scrollbar(frame, orient="vertical")
        sb.pack(side="right", fill="y")
        tree = ttk.Treeview(frame, columns=("rank","name","score"),
                            show="headings", yscrollcommand=sb.set)
        tree.heading("rank", text="Rank")
        tree.heading("name", text="Player")
        tree.heading("score", text="Score")
        tree.column("rank", width=60, anchor="center")
        tree.column("name", width=220, anchor="center")
        tree.column("score", width=100, anchor="center")
        tree.pack(side="left", fill="both", expand=True)
        sb.config(command=tree.yview)
        medals = ["🥇","🥈","🥉"]
        for i, p in enumerate(sp):
            r = medals[i] if i < 3 else str(i+1)
            tree.insert("", "end", values=(r, p["name"], f"{p['score']:.1f}"))


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app  = IPLAnalyzer(root)
    root.mainloop()

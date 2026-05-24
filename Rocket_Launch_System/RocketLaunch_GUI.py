import subprocess
import threading
import os
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


APP_DIR = Path(__file__).resolve().parent
DEFAULT_EXE = APP_DIR / "output" / "Main.exe"


class RocketLaunchGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Rocket Launch System")
        self.geometry("1180x760")
        self.minsize(1040, 700)

        self._stage_vars = []
        self._stage_rows = []
        self._run_thread = None

        self._build_style()
        self._build_layout()
        self._set_stage_count(3)

    def _build_style(self):
        self.configure(bg="#0f172a")
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("App.TFrame", background="#0f172a")
        style.configure("Card.TFrame", background="#111827", relief="flat")
        style.configure("Title.TLabel", background="#0f172a", foreground="#f8fafc", font=("Segoe UI", 20, "bold"))
        style.configure("Subtitle.TLabel", background="#0f172a", foreground="#94a3b8", font=("Segoe UI", 10))
        style.configure("Section.TLabelframe", background="#111827", foreground="#e2e8f0", padding=12)
        style.configure("Section.TLabelframe.Label", background="#111827", foreground="#e2e8f0", font=("Segoe UI", 10, "bold"))
        style.configure("Section.TLabel", background="#111827", foreground="#cbd5e1", font=("Segoe UI", 9))
        style.configure("Card.TLabel", background="#111827", foreground="#cbd5e1", font=("Segoe UI", 9))
        style.configure("Card.TEntry", fieldbackground="#1f2937", background="#1f2937", foreground="#f8fafc", insertcolor="#f8fafc")
        style.configure("Card.TCombobox", fieldbackground="#1f2937", background="#1f2937", foreground="#f8fafc")
        style.configure("Card.TSpinbox", fieldbackground="#1f2937", background="#1f2937", foreground="#f8fafc")
        style.configure("Accent.TButton", background="#2563eb", foreground="#ffffff", padding=(14, 8), borderwidth=0)
        style.map("Accent.TButton", background=[("active", "#1d4ed8")])
        style.configure("Neutral.TButton", background="#334155", foreground="#ffffff", padding=(14, 8), borderwidth=0)
        style.map("Neutral.TButton", background=[("active", "#475569")])

    def _build_layout(self):
        header = ttk.Frame(self, style="App.TFrame")
        header.pack(fill="x", padx=24, pady=(20, 12))

        ttk.Label(header, text="Rocket Launch System", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Inserisci i parametri della simulazione, avvia il motore C e lascia che i grafici vengano generati automaticamente.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        body = ttk.Frame(self, style="App.TFrame")
        body.pack(fill="both", expand=True, padx=24, pady=(0, 18))
        body.columnconfigure(0, weight=2)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        left_panel = ttk.Frame(body, style="App.TFrame")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left_panel.rowconfigure(1, weight=1)
        left_panel.columnconfigure(0, weight=1)

        right_panel = ttk.Frame(body, style="App.TFrame")
        right_panel.grid(row=0, column=1, sticky="nsew")
        right_panel.rowconfigure(1, weight=1)
        right_panel.columnconfigure(0, weight=1)

        self._build_general_section(left_panel)
        self._build_stages_section(left_panel)
        self._build_actions_section(left_panel)
        self._build_console_section(right_panel)

    def _build_general_section(self, parent):
        section = ttk.Labelframe(parent, text="Parametri generali", style="Section.TLabelframe")
        section.grid(row=0, column=0, sticky="ew")
        section.columnconfigure(0, weight=1)
        section.columnconfigure(1, weight=1)
        section.columnconfigure(2, weight=1)

        for i in range(3):
            section.columnconfigure(i, weight=1)

        self.drag_coeff = tk.StringVar(value="0.5")
        self.ref_area = tk.StringVar(value="10.75")
        self.alt_start = tk.StringVar(value="0.0")
        self.mission = tk.StringVar(value="Orbit")
        self.sim_time = tk.StringVar(value="900")
        self.stage_count = tk.IntVar(value=3)
        self.exe_path = tk.StringVar(value=str(DEFAULT_EXE))

        self._add_field(section, 0, 0, "Drag coefficient", self.drag_coeff)
        self._add_field(section, 0, 1, "Reference area (m^2)", self.ref_area)
        self._add_field(section, 0, 2, "Starting altitude (m)", self.alt_start)

        self._add_field(section, 2, 0, "Simulation time (s)", self.sim_time)

        ttk.Label(section, text="Missione", style="Section.TLabel").grid(row=2, column=1, sticky="w", pady=(0, 4), padx=(8, 4))
        mission_box = ttk.Combobox(
            section,
            textvariable=self.mission,
            values=("Orbit", "Escape"),
            state="readonly",
            style="Card.TCombobox",
        )
        mission_box.grid(row=3, column=1, sticky="ew", padx=(8, 4), pady=(0, 8))

        ttk.Label(section, text="Numero stadi", style="Section.TLabel").grid(row=2, column=2, sticky="w", pady=(0, 4), padx=(8, 4))
        stage_spin = ttk.Spinbox(section, from_=1, to=20, textvariable=self.stage_count, width=8, style="Card.TSpinbox", command=self._on_stage_count_changed)
        stage_spin.grid(row=3, column=2, sticky="w", padx=(8, 4), pady=(0, 8))
        stage_spin.bind("<Return>", lambda _event: self._on_stage_count_changed())
        stage_spin.bind("<FocusOut>", lambda _event: self._on_stage_count_changed())

        ttk.Label(section, text="Main.exe", style="Section.TLabel").grid(row=4, column=0, columnspan=3, sticky="w", pady=(0, 4), padx=(8, 4))
        exe_row = ttk.Frame(section, style="Card.TFrame")
        exe_row.grid(row=5, column=0, columnspan=3, sticky="ew", padx=(8, 4), pady=(0, 4))
        exe_row.columnconfigure(0, weight=1)

        exe_entry = ttk.Entry(exe_row, textvariable=self.exe_path, style="Card.TEntry")
        exe_entry.grid(row=0, column=0, sticky="ew")
        ttk.Button(exe_row, text="Sfoglia", style="Neutral.TButton", command=self._browse_executable).grid(row=0, column=1, padx=(8, 0))

    def _build_stages_section(self, parent):
        section = ttk.Labelframe(parent, text="Stadi del razzo", style="Section.TLabelframe")
        section.grid(row=1, column=0, sticky="nsew", pady=12)
        section.columnconfigure(0, weight=1)
        section.rowconfigure(1, weight=1)

        header = ttk.Frame(section, style="Card.TFrame")
        header.grid(row=0, column=0, sticky="ew", padx=4, pady=(0, 8))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="Ogni riga corrisponde a uno stadio della simulazione.", style="Card.TLabel").grid(row=0, column=0, sticky="w")

        canvas = tk.Canvas(section, bg="#111827", highlightthickness=0)
        scrollbar = ttk.Scrollbar(section, orient="vertical", command=canvas.yview)
        self.stages_container = ttk.Frame(canvas, style="Card.TFrame")

        self._stages_window = canvas.create_window((0, 0), window=self.stages_container, anchor="nw")

        def _sync_scroll_region(_event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _sync_inner_width(event):
            canvas.itemconfigure(self._stages_window, width=event.width)

        self.stages_container.bind("<Configure>", _sync_scroll_region)
        canvas.bind("<Configure>", _sync_inner_width)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=1, column=0, sticky="nsew")
        scrollbar.grid(row=1, column=1, sticky="ns")

    def _build_actions_section(self, parent):
        section = ttk.Frame(parent, style="App.TFrame")
        section.grid(row=2, column=0, sticky="ew")
        section.columnconfigure(0, weight=1)

        actions = ttk.Frame(section, style="App.TFrame")
        actions.grid(row=0, column=0, sticky="ew")
        actions.columnconfigure(0, weight=1)

        ttk.Button(actions, text="Aggiorna stadi", style="Neutral.TButton", command=self._sync_stage_count).grid(row=0, column=0, sticky="w")
        ttk.Button(actions, text="Avvia simulazione", style="Accent.TButton", command=self._start_simulation).grid(row=0, column=1, sticky="e", padx=(10, 0))

        self.status_var = tk.StringVar(value="Pronto.")
        ttk.Label(section, textvariable=self.status_var, style="Subtitle.TLabel").grid(row=1, column=0, sticky="w", pady=(8, 0))

    def _build_console_section(self, parent):
        section = ttk.Labelframe(parent, text="Output esecuzione", style="Section.TLabelframe")
        section.grid(row=0, column=0, sticky="nsew")
        section.rowconfigure(0, weight=1)
        section.columnconfigure(0, weight=1)

        self.console = tk.Text(
            section,
            wrap="word",
            bg="#020617",
            fg="#dbeafe",
            insertbackground="#dbeafe",
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            font=("Consolas", 10),
        )
        self.console.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(section, orient="vertical", command=self.console.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.console.configure(yscrollcommand=scrollbar.set)

    def _add_field(self, parent, row, column, label_text, variable):
        ttk.Label(parent, text=label_text, style="Section.TLabel").grid(row=row, column=column, sticky="w", pady=(0, 4), padx=(8, 4))
        entry = ttk.Entry(parent, textvariable=variable, style="Card.TEntry")
        entry.grid(row=row + 1, column=column, sticky="ew", padx=(8, 4), pady=(0, 8))
        return entry

    def _browse_executable(self):
        selected = filedialog.askopenfilename(
            title="Seleziona Main.exe",
            initialdir=str(DEFAULT_EXE.parent if DEFAULT_EXE.parent.exists() else APP_DIR),
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")],
        )
        if selected:
            self.exe_path.set(selected)

    def _sync_stage_count(self):
        try:
            count = int(self.stage_count.get())
        except tk.TclError:
            messagebox.showerror("Errore", "Il numero di stadi non e valido.")
            return

        if count < 1:
            messagebox.showerror("Errore", "Il numero di stadi deve essere almeno 1.")
            return

        self._set_stage_count(count)

    def _on_stage_count_changed(self):
        self.after_idle(self._sync_stage_count)

    def _set_stage_count(self, count):
        for widget in self.stages_container.winfo_children():
            widget.destroy()

        self._stage_vars = []
        self._stage_rows = []

        field_specs = [
            ("Dry mass (kg)", "1000"),
            ("Fuel mass (kg)", "500"),
            ("Thrust (N)", "200000"),
            ("Burn time (s)", "60"),
            ("Target pitch (deg)", "90"),
            ("Change rate (deg/s)", "1"),
        ]

        for index in range(count):
            stage_frame = ttk.Labelframe(self.stages_container, text=f"Stadio {index + 1}", style="Section.TLabelframe")
            stage_frame.grid(row=index, column=0, sticky="ew", padx=2, pady=8)
            for col_index in range(3):
                stage_frame.columnconfigure(col_index, weight=1)

            defaults = [tk.StringVar(value=default) for _label, default in field_specs]
            self._stage_vars.append(defaults)

            entries = []
            for field_index, ((label_text, _default), variable) in enumerate(zip(field_specs, defaults)):
                row_offset = 0 if field_index < 3 else 2
                column_offset = field_index % 3
                ttk.Label(stage_frame, text=label_text, style="Card.TLabel").grid(row=row_offset, column=column_offset, sticky="w", padx=6, pady=(0, 4))
                entry = ttk.Entry(stage_frame, textvariable=variable, style="Card.TEntry")
                entry.grid(row=row_offset + 1, column=column_offset, sticky="ew", padx=6, pady=(0, 8))
                entries.append(entry)
            self._stage_rows.append(entries)

        self.stage_count.set(count)
        self.status_var.set(f"Configurati {count} stadi.")

    def _collect_float(self, variable, field_name):
        try:
            return float(variable.get())
        except (tk.TclError, ValueError):
            raise ValueError(f"Campo non valido: {field_name}")

    def _collect_inputs(self):
        exe_path = Path(self.exe_path.get().strip().strip('"'))
        if not exe_path.exists():
            raise FileNotFoundError(f"Eseguibile non trovato: {exe_path}")

        mission_value = 1 if self.mission.get() == "Orbit" else 2
        stage_count = int(self.stage_count.get())

        payload_lines = [
            f"{self._collect_float(self.drag_coeff, 'Drag coefficient')}",
            f"{self._collect_float(self.ref_area, 'Reference area')}",
            f"{self._collect_float(self.alt_start, 'Starting altitude')}",
            f"{stage_count}",
        ]

        for index, stage_vars in enumerate(self._stage_vars, start=1):
            field_names = [
                "Dry mass",
                "Fuel mass",
                "Thrust",
                "Burn time",
                "Target pitch",
                "Change rate",
            ]
            values = [self._collect_float(variable, f"Stadio {index} - {field_name}") for variable, field_name in zip(stage_vars, field_names)]
            payload_lines.extend(f"{value}" for value in values)

        payload_lines.extend([f"{mission_value}", f"{self._collect_float(self.sim_time, 'Simulation time')}"])
        csv_path = exe_path.parent / "simulation_results.csv"
        images_dir = exe_path.parent / "images"
        return exe_path, csv_path, images_dir, "\n".join(payload_lines) + "\n"

    def _start_simulation(self):
        if self._run_thread and self._run_thread.is_alive():
            messagebox.showinfo("Simulazione in corso", "Attendi il completamento della simulazione corrente.")
            return

        try:
            exe_path, csv_path, images_dir, payload = self._collect_inputs()
        except Exception as exc:
            messagebox.showerror("Input non valido", str(exc))
            return

        self.console.delete("1.0", tk.END)
        self._append_console(f"Avvio di {exe_path}\n")
        self.status_var.set("Simulazione in corso...")

        self._run_thread = threading.Thread(target=self._run_simulation, args=(exe_path, csv_path, images_dir, payload), daemon=True)
        self._run_thread.start()
        self.after(100, self._poll_thread)

    def _poll_thread(self):
        if self._run_thread and self._run_thread.is_alive():
            self.after(100, self._poll_thread)

    def _run_simulation(self, exe_path, csv_path, images_dir, payload):
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
            result = subprocess.run(
                [str(exe_path), "--cli"],
                input=payload,
                text=True,
                capture_output=True,
                cwd=str(exe_path.parent),
                creationflags=creationflags,
            )
        except Exception as exc:
            self.after(0, lambda: self._finish_run(error=f"Errore durante l'esecuzione: {exc}"))
            return

        output = []
        if result.stdout:
            output.append(result.stdout.strip())
        if result.stderr:
            output.append(result.stderr.strip())

        message = "\n\n".join(text for text in output if text)

        graph_output = self._generate_graphs(csv_path, images_dir) if result.returncode == 0 else ""
        if graph_output:
            message = "\n\n".join(text for text in [message, graph_output] if text)

        self.after(
            0,
            lambda: self._finish_run(
                returncode=result.returncode,
                output=message,
            ),
        )

    def _generate_graphs(self, csv_path, images_dir):
        outputs = []
        images_dir.mkdir(parents=True, exist_ok=True)

        for script_name in ("Trajectory_Graph.py", "Grafic_Result.py"):
            script_path = APP_DIR / script_name
            try:
                result = subprocess.run(
                    [sys.executable, str(script_path), str(csv_path), str(images_dir)],
                    text=True,
                    capture_output=True,
                    cwd=str(APP_DIR),
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
                )
            except Exception as exc:
                outputs.append(f"{script_name}: {exc}")
                continue

            combined = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part and part.strip())
            if combined:
                outputs.append(combined)

        for image_path in sorted(images_dir.glob("*.png")):
            try:
                os.startfile(str(image_path))
            except OSError:
                pass

        return "\n\n".join(outputs)

    def _finish_run(self, returncode=None, output="", error=None):
        if output:
            self._append_console(output + "\n")
        if error is not None:
            self._append_console(error + "\n")
            self.status_var.set("Errore.")
            messagebox.showerror("Errore", error)
            return

        if returncode == 0:
            self._append_console("Simulazione completata. I grafici dovrebbero aprirsi automaticamente.\n")
            self.status_var.set("Simulazione completata.")
            messagebox.showinfo("Completato", "Simulazione completata con successo.")
        else:
            self._append_console(f"Il processo ha restituito il codice {returncode}.\n")
            self.status_var.set("Errore durante la simulazione.")
            messagebox.showerror("Errore", f"Il processo ha restituito il codice {returncode}.")

    def _append_console(self, text):
        self.console.insert(tk.END, text)
        self.console.see(tk.END)


if __name__ == "__main__":
    app = RocketLaunchGUI()
    app.mainloop()
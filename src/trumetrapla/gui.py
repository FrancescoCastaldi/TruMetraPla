"""Componenti dell'interfaccia grafica di TruMetraPla."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Mapping, Protocol

from .data_loader import (
    ColumnMappingError,
    OPTIONAL_FIELDS,
    REQUIRED_FIELDS,
    load_operations_from_excel,
    suggest_column_mapping,
)
from .metrics import group_by_employee, group_by_process, summarize_operations
from .models import OperationRecord


class GUIUnavailableError(RuntimeError):
    """Errore sollevato quando non è possibile avviare la GUI."""


class _TkRoot(Protocol):
    def title(self, value: str) -> None: ...

    def geometry(self, value: str) -> None: ...

    def minsize(self, width: int, height: int) -> None: ...

    def resizable(self, width: bool, height: bool) -> None: ...

    def configure(self, **kwargs: object) -> None: ...

    def config(self, **kwargs: object) -> None: ...

    def mainloop(self) -> None: ...

    def destroy(self) -> None: ...


@dataclass
class _Toolkit:
    tk: object
    ttk: object
    messagebox: object
    filedialog: object


@dataclass
class _AppState:
    """Stato condiviso dell'interfaccia grafica."""

    records: list[OperationRecord] = field(default_factory=list)
    filtered_records: list[OperationRecord] = field(default_factory=list)
    file_path: Path | None = None


@dataclass
class WelcomeWindowHandles:
    """Informazioni utili per i test sulla finestra creata."""

    root: _TkRoot
    state: _AppState
    commands: Mapping[str, Callable[[], None]]


def _load_toolkit() -> _Toolkit:
    try:
        import tkinter as tk  # type: ignore
        from tkinter import filedialog, messagebox, ttk  # type: ignore
    except ModuleNotFoundError as exc:
        raise GUIUnavailableError(
            "Tkinter non è disponibile in questo ambiente: installa il runtime grafico di Windows."
        ) from exc
    except Exception as exc:  # pragma: no cover - percorso imprevisto
        raise GUIUnavailableError("Impossibile inizializzare Tkinter.") from exc

    return _Toolkit(tk=tk, ttk=ttk, messagebox=messagebox, filedialog=filedialog)


def launch_welcome_window(
    root_factory: Callable[[], _TkRoot] | None = None,
    *,
    run_mainloop: bool = True,
    operations_loader: Callable[[Path], list[OperationRecord]] | None = None,
    _toolkit: Dict[str, object] | None = None,
) -> WelcomeWindowHandles | None:
    """Mostra la finestra grafica principale di TruMetraPla."""

    if _toolkit is None:
        toolkit = _load_toolkit()
    else:
        try:
            toolkit = _Toolkit(
                tk=_toolkit["tk"],
                ttk=_toolkit["ttk"],
                messagebox=_toolkit["messagebox"],
                filedialog=_toolkit["filedialog"],
            )
        except KeyError as exc:  # pragma: no cover - uso errato del parametro privato
            raise GUIUnavailableError("Toolkit grafico incompleto.") from exc

        if (
            toolkit.tk is None
            or toolkit.ttk is None
            or toolkit.messagebox is None
            or toolkit.filedialog is None
        ):
            raise GUIUnavailableError("Toolkit grafico non valido.")

    tk = toolkit.tk
    ttk = toolkit.ttk
    messagebox = toolkit.messagebox
    filedialog = toolkit.filedialog

    if root_factory is None:
        root: _TkRoot = tk.Tk()
    else:
        root = root_factory()

    root.title("TruMetraPla - Console Analitica")
    root.geometry("960x600")
    try:
        root.minsize(860, 520)
    except Exception:  # pragma: no cover - alcuni stub potrebbero non implementare minsize
        pass
    root.resizable(True, True)

    try:
        root.configure(background="#f4f5f7")
    except Exception:  # pragma: no cover - alcuni stub di test non implementano configure
        pass

    state = _AppState()
    loader = operations_loader or (lambda path: load_operations_from_excel(path))

    # Variabili di stato testuali
    file_var = tk.StringVar(value="Nessun file Excel aperto")
    summary_var = tk.StringVar(value="Carica un file per visualizzare i KPI")
    status_var = tk.StringVar(value="Pronto")

    # Menu principale
    menubar = tk.Menu(root)
    file_menu = tk.Menu(menubar, tearoff=0)
    tools_menu = tk.Menu(menubar, tearoff=0)
    help_menu = tk.Menu(menubar, tearoff=0)

    def _update_table(records: list[OperationRecord]) -> None:
        tree.delete(*tree.get_children())
        for record in records:
            tree.insert(
                "",
                "end",
                values=(
                    record.date.strftime("%d/%m/%Y"),
                    record.employee,
                    record.process,
                    record.process_type or "-",
                    record.machine or "-",
                    f"{record.quantity}",
                    f"{record.duration_minutes:.1f}",
                    f"{record.productivity_per_hour:.2f}",
                ),
            )

    def _format_summary(records: list[OperationRecord]) -> str:
        if not records:
            return "Nessun dato disponibile"

        summary = summarize_operations(records)
        machines = len({record.machine for record in records if record.machine})
        process_types = len(
            {record.process_type for record in records if record.process_type}
        )
        return (
            "Record: {records} | Quantità totali: {qty} | Ore totali: {hours:.2f} | "
            "Throughput medio: {throughput:.2f} pezzi/ora | Dipendenti: {employees} | "
            "Processi: {processes} | Macchine: {machines} | Tipi processo: {process_types}"
        ).format(
            records=len(records),
            qty=summary.total_quantity,
            hours=summary.total_hours,
            throughput=summary.throughput,
            employees=summary.employees,
            processes=summary.processes,
            machines=machines,
            process_types=process_types,
        )

    def _apply_filters() -> None:
        employee_value = employee_var.get()
        process_value = process_var.get()
        machine_value = machine_var.get()
        process_type_value = process_type_var.get()

        filtered = [
            record
            for record in state.records
            if (employee_value in {"", "Tutti"} or record.employee == employee_value)
            and (process_value in {"", "Tutti"} or record.process == process_value)
            and (machine_value in {"", "Tutti", "Tutte"} or record.machine == machine_value)
            and (
                process_type_value in {"", "Tutti", "Tutte"}
                or record.process_type == process_type_value
            )
        ]

        state.filtered_records = filtered
        _update_table(filtered)
        summary_var.set(_format_summary(filtered))

    def _refresh_filters(records: list[OperationRecord]) -> None:
        employees = sorted({record.employee for record in records})
        processes = sorted({record.process for record in records})
        machines = sorted({record.machine for record in records if record.machine})
        process_types = sorted(
            {record.process_type for record in records if record.process_type}
        )

        employee_combo.configure(values=["Tutti"] + employees)
        process_combo.configure(values=["Tutti"] + processes)
        machine_combo.configure(values=["Tutte"] + machines if machines else ["Tutte"])
        process_type_combo.configure(
            values=["Tutte"] + process_types if process_types else ["Tutte"]
        )
        employee_combo.current(0)
        process_combo.current(0)
        machine_combo.current(0)
        process_type_combo.current(0)
        state.filtered_records = records

    def _prompt_column_mapping(excel_path: Path) -> dict[str, str] | None:
        try:
            import pandas as pd
        except ModuleNotFoundError as exc:  # pragma: no cover - dipendenza obbligatoria
            messagebox.showerror(
                "Pandas non disponibile",
                "Installa la dipendenza 'pandas' per importare file Excel.",
            )
            raise GUIUnavailableError("Pandas richiesto per la gestione dei file Excel") from exc

        try:
            preview = pd.read_excel(excel_path, sheet_name=0, nrows=0)
        except Exception as exc:  # pragma: no cover - errori di I/O imprevisti
            messagebox.showerror(
                "Errore di lettura",
                f"Impossibile leggere le intestazioni del file: {exc}",
            )
            return None

        columns = list(preview.columns)
        if not columns:
            messagebox.showerror(
                "Intestazioni mancanti",
                "Il file Excel selezionato non contiene alcuna intestazione di colonna.",
            )
            return None

        suggestions, _missing = suggest_column_mapping(columns)
        option_values = ["(Seleziona)"] + columns

        field_labels: dict[str, str] = {
            "date": "Data (obbligatoria)",
            "employee": "Dipendente",
            "process": "Processo",
            "machine": "Macchina (facoltativa)",
            "process_type": "Tipo processo (facoltativo)",
            "quantity": "Quantità prodotta",
            "duration_minutes": "Durata in minuti",
        }

        dialog = tk.Toplevel(root)
        dialog.title("Associa colonne Excel")
        dialog.geometry("480x360")
        dialog.transient(root)

        container = ttk.Frame(dialog, padding=16)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text=(
                "Abbina i campi richiesti alle colonne del file Excel."
                " Le scelte verranno salvate per questa importazione."
            ),
            wraplength=430,
            justify="left",
        ).pack(fill="x", pady=(0, 12))

        mapping_vars: dict[str, object] = {}

        optional_fields = set(OPTIONAL_FIELDS)
        for field in list(REQUIRED_FIELDS) + list(OPTIONAL_FIELDS):
            row = ttk.Frame(container)
            row.pack(fill="x", pady=4)
            ttk.Label(row, text=field_labels[field]).pack(anchor="w")
            var = tk.StringVar()
            values = option_values
            if field in optional_fields:
                values = ["(Facoltativo)"] + columns
            combo = ttk.Combobox(
                row,
                state="readonly",
                values=values,
                textvariable=var,
                width=36,
            )
            suggestion = suggestions.get(field)
            if suggestion and suggestion in columns:
                combo.current(values.index(suggestion))
            else:
                combo.current(0)
            combo.pack(fill="x", pady=(2, 0))
            mapping_vars[field] = var

        feedback_var = tk.StringVar(value="")
        feedback = ttk.Label(container, textvariable=feedback_var, foreground="#b3261e")
        feedback.pack(fill="x", pady=(8, 0))

        actions = ttk.Frame(container)
        actions.pack(fill="x", pady=(16, 0))
        actions.pack_propagate(False)

        result: dict[str, str] | None = None

        def _confirm() -> None:
            nonlocal result
            selections: dict[str, str] = {}
            used_columns: set[str] = set()

            for field, var in mapping_vars.items():
                value = var.get()
                if field in optional_fields and value == "(Facoltativo)":
                    continue
                if value == "(Seleziona)":
                    feedback_var.set("Completa la selezione di tutte le colonne richieste.")
                    return
                if value in used_columns:
                    feedback_var.set(
                        "Ogni colonna può essere assegnata a un solo campo. Rivedi la selezione."
                    )
                    return
                used_columns.add(value)
                selections[field] = value

            result = selections
            dialog.destroy()

        def _cancel() -> None:
            result = None
            dialog.destroy()

        ttk.Button(actions, text="Annulla", command=_cancel).pack(side="right", padx=(0, 8))
        ttk.Button(actions, text="OK", command=_confirm).pack(side="right")

        try:
            dialog.grab_set()
        except Exception:  # pragma: no cover - alcuni ambienti headless
            pass
        dialog.focus_force()

        if hasattr(root, "wait_window"):
            root.wait_window(dialog)
        else:  # pragma: no cover - fallback per stub di test
            dialog.mainloop()

        return result

    def _open_file() -> None:
        path_str = filedialog.askopenfilename(
            title="Seleziona un file Excel",
            filetypes=(
                ("File Excel", "*.xlsx *.xlsm *.xls *.xlsb"),
                ("Tutti i file", "*.*"),
            ),
        )

        if not path_str:
            return

        excel_path = Path(path_str)

        try:
            records = loader(excel_path)
        except FileNotFoundError:
            messagebox.showerror("File non trovato", f"Il file {excel_path} non esiste.")
            return
        except ColumnMappingError:
            mapping = _prompt_column_mapping(excel_path)
            if not mapping:
                status_var.set("Importazione annullata: abbina le colonne richieste.")
                return
            try:
                records = load_operations_from_excel(excel_path, column_mapping=mapping)
            except ColumnMappingError as exc:
                messagebox.showerror("Colonne mancanti", str(exc))
                return
            except Exception as exc:  # pragma: no cover - errori imprevisti
                messagebox.showerror("Errore", f"Impossibile leggere il file: {exc}")
                return
        except Exception as exc:  # pragma: no cover - errori imprevisti
            messagebox.showerror("Errore", f"Impossibile leggere il file: {exc}")
            return

        state.records = records
        state.file_path = excel_path
        file_var.set(f"File corrente: {excel_path}")
        status_var.set(f"Caricate {len(records)} righe dal file Excel")
        _refresh_filters(records)
        _apply_filters()

    def _show_kpi_dialog() -> None:
        if not state.filtered_records:
            messagebox.showinfo(
                "Nessun dato",
                "Carica un file Excel e applica eventuali filtri per visualizzare i KPI.",
            )
            return

        summary = summarize_operations(state.filtered_records)
        top_employees = group_by_employee(state.filtered_records)[:3]
        top_processes = group_by_process(state.filtered_records)[:3]

        def _format_entities(entities: list) -> str:
            if not entities:
                return "Nessuno"
            return "\n".join(
                f"- {item.entity}: {item.total_quantity} pezzi ({item.throughput:.2f} pz/ora)"
                for item in entities
            )

        message = (
            "Quantità totali: {qty}\n"
            "Ore totali: {hours:.2f}\n"
            "Throughput medio: {throughput:.2f} pezzi/ora\n"
            "Dipendenti unici: {employees}\n"
            "Processi monitorati: {processes}\n\n"
            "Top dipendenti:\n{top_employees}\n\n"
            "Top processi:\n{top_processes}"
        ).format(
            qty=summary.total_quantity,
            hours=summary.total_hours,
            throughput=summary.throughput,
            employees=summary.employees,
            processes=summary.processes,
            top_employees=_format_entities(top_employees),
            top_processes=_format_entities(top_processes),
        )

        messagebox.showinfo("KPI principali", message)

    def _show_pie_chart() -> None:
        records = state.filtered_records or state.records
        if not records:
            messagebox.showinfo(
                "Nessun dato",
                "Carica un file Excel e applica eventuali filtri per generare il grafico.",
            )
            return

        try:
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure
        except ModuleNotFoundError:  # pragma: no cover - dipendenza opzionale
            messagebox.showerror(
                "Matplotlib non disponibile",
                "Installa la dipendenza opzionale 'matplotlib' per visualizzare i grafici.",
            )
            return
        except Exception as exc:  # pragma: no cover - errori imprevisti
            messagebox.showerror(
                "Errore grafico",
                f"Impossibile inizializzare il motore di grafici: {exc}",
            )
            return

        chart_window = tk.Toplevel(root)
        chart_window.title("Report grafico TruMetraPla")
        chart_window.geometry("720x520")
        try:
            chart_window.minsize(560, 420)
        except Exception:  # pragma: no cover - alcuni stub non implementano minsize
            pass

        container = ttk.Frame(chart_window, padding=16)
        container.pack(fill="both", expand=True)

        heading = ttk.Label(
            container,
            text="Distribuzione dei pezzi prodotti",
            font=("Segoe UI", 12, "bold"),
        )
        heading.pack(anchor="w")

        options_frame = ttk.Frame(container)
        options_frame.pack(fill="x", pady=(12, 8))

        ttk.Label(options_frame, text="Raggruppa per:").pack(side="left")

        grouping_combo = ttk.Combobox(
            options_frame,
            state="readonly",
            values=["Processo", "Dipendente"],
            width=20,
        )
        grouping_combo.current(0)
        grouping_combo.pack(side="left", padx=8)

        figure = Figure(figsize=(5.8, 4.2), dpi=100)
        axis = figure.add_subplot(111)
        canvas = FigureCanvasTkAgg(figure, master=container)
        canvas.get_tk_widget().pack(fill="both", expand=True)

        info_var = tk.StringVar(value="")
        ttk.Label(container, textvariable=info_var, wraplength=660, justify="center").pack(
            fill="x", pady=(8, 0)
        )

        def _refresh_chart(*_args: object) -> None:
            selected = grouping_combo.get()
            if selected == "Dipendente":
                breakdown = group_by_employee(records)
                title = "Distribuzione pezzi per dipendente"
            else:
                breakdown = group_by_process(records)
                title = "Distribuzione pezzi per processo"

            filtered_breakdown = [
                item for item in breakdown if item.total_quantity > 0
            ]

            if not filtered_breakdown:
                info_var.set(
                    "Non sono disponibili dati con quantità positive per il grafico selezionato."
                )
                axis.clear()
                canvas.draw_idle()
                return

            info_var.set("")
            axis.clear()

            values = [item.total_quantity for item in filtered_breakdown]
            labels = [item.entity for item in filtered_breakdown]
            total = sum(values)

            def _format_pct(pct: float) -> str:
                absolute = int(round(pct * total / 100.0))
                return f"{pct:.1f}% ({absolute} pezzi)"

            axis.pie(
                values,
                labels=labels,
                autopct=_format_pct,
                startangle=90,
            )
            axis.set_title(title)
            axis.axis("equal")
            canvas.draw_idle()

        grouping_combo.bind("<<ComboboxSelected>>", _refresh_chart)
        _refresh_chart()

    file_menu.add_command(label="Apri file Excel…", command=_open_file)
    file_menu.add_separator()
    file_menu.add_command(label="Esci", command=root.destroy)

    tools_menu.add_command(label="Mostra KPI filtrati", command=_show_kpi_dialog)
    tools_menu.add_command(label="Grafico a torta", command=_show_pie_chart)

    def _open_docs() -> None:
        import webbrowser

        webbrowser.open(
            "https://github.com/FrancescoCastaldi/TruMetraPla#readme",
            new=2,
        )

    help_menu.add_command(label="Documentazione", command=_open_docs)

    menubar.add_cascade(label="File", menu=file_menu)
    menubar.add_cascade(label="Strumenti", menu=tools_menu)
    menubar.add_cascade(label="Aiuto", menu=help_menu)

    try:
        root.config(menu=menubar)
    except Exception:  # pragma: no cover - alcuni stub potrebbero non implementare config
        pass

    # Layout principale
    main_frame = ttk.Frame(root, padding=16)
    main_frame.pack(expand=True, fill="both")

    header = ttk.Frame(main_frame)
    header.pack(fill="x")

    ttk.Label(header, textvariable=file_var, font=("Segoe UI", 11, "bold"), anchor="w").pack(
        fill="x", pady=(0, 4)
    )
    ttk.Label(header, textvariable=summary_var, wraplength=920, anchor="w").pack(
        fill="x"
    )

    filters_frame = ttk.Frame(main_frame)
    filters_frame.pack(fill="x", pady=12)

    employee_var = tk.StringVar(value="Tutti")
    process_var = tk.StringVar(value="Tutti")
    machine_var = tk.StringVar(value="Tutte")
    process_type_var = tk.StringVar(value="Tutte")

    ttk.Label(filters_frame, text="Dipendente:").pack(side="left", padx=(0, 6))
    employee_combo = ttk.Combobox(
        filters_frame, width=28, state="readonly", textvariable=employee_var
    )
    employee_combo.pack(side="left")
    employee_combo.configure(values=["Tutti"])
    employee_combo.current(0)

    ttk.Label(filters_frame, text="Processo:").pack(side="left", padx=(16, 6))
    process_combo = ttk.Combobox(
        filters_frame, width=28, state="readonly", textvariable=process_var
    )
    process_combo.pack(side="left")
    process_combo.configure(values=["Tutti"])
    process_combo.current(0)

    ttk.Label(filters_frame, text="Macchina:").pack(side="left", padx=(16, 6))
    machine_combo = ttk.Combobox(
        filters_frame, width=24, state="readonly", textvariable=machine_var
    )
    machine_combo.pack(side="left")
    machine_combo.configure(values=["Tutte"])
    machine_combo.current(0)

    ttk.Label(filters_frame, text="Tipo processo:").pack(side="left", padx=(16, 6))
    process_type_combo = ttk.Combobox(
        filters_frame,
        width=24,
        state="readonly",
        textvariable=process_type_var,
    )
    process_type_combo.pack(side="left")
    process_type_combo.configure(values=["Tutte"])
    process_type_combo.current(0)

    filter_button = ttk.Button(filters_frame, text="Applica filtri", command=_apply_filters)
    filter_button.pack(side="left", padx=(16, 0))

    table_frame = ttk.Frame(main_frame)
    table_frame.pack(fill="both", expand=True)

    columns = (
        "date",
        "employee",
        "process",
        "process_type",
        "machine",
        "quantity",
        "duration",
        "throughput",
    )
    tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        height=15,
    )

    headings = {
        "date": "Data",
        "employee": "Dipendente",
        "process": "Processo",
        "process_type": "Tipo processo",
        "machine": "Macchina",
        "quantity": "Pezzi",
        "duration": "Durata (min)",
        "throughput": "Pezzi/ora",
    }

    for column in columns:
        tree.heading(column, text=headings[column])
        anchor = "center"
        if column in {"employee", "process", "process_type", "machine"}:
            anchor = "w"
        width = 140
        if column in {"quantity", "duration", "throughput"}:
            width = 110
        tree.column(column, anchor=anchor, width=width)

    vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="left", fill="y")
    hsb.pack(side="bottom", fill="x")

    footer = ttk.Frame(main_frame)
    footer.pack(fill="x", pady=(12, 0))

    ttk.Button(footer, text="Apri file Excel…", command=_open_file).pack(side="left")
    ttk.Button(footer, text="Mostra KPI", command=_show_kpi_dialog).pack(side="left", padx=8)
    ttk.Button(footer, text="Grafico a torta", command=_show_pie_chart).pack(
        side="left", padx=8
    )
    ttk.Label(footer, textvariable=status_var).pack(side="right")

    ttk.Label(
        main_frame,
        text="Prodotto da Francesco Castaldi",
        anchor="center",
    ).pack(fill="x", pady=(8, 0))

    employee_combo.bind("<<ComboboxSelected>>", lambda *_: _apply_filters())
    process_combo.bind("<<ComboboxSelected>>", lambda *_: _apply_filters())
    machine_combo.bind("<<ComboboxSelected>>", lambda *_: _apply_filters())
    process_type_combo.bind("<<ComboboxSelected>>", lambda *_: _apply_filters())

    commands: dict[str, Callable[[], None]] = {
        "open_file": _open_file,
        "show_kpi": _show_kpi_dialog,
        "show_chart": _show_pie_chart,
        "apply_filters": _apply_filters,
    }

    if run_mainloop:
        root.mainloop()
        return None

    return WelcomeWindowHandles(root=root, state=state, commands=commands)

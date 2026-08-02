"""TruMetraPla - Graphical user interface components."""

from __future__ import annotations

from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
import re
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
    """Error raised when the GUI cannot be started."""


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
    """Shared state of the graphical interface."""

    records: list[OperationRecord] = field(default_factory=list)
    filtered_records: list[OperationRecord] = field(default_factory=list)
    file_path: Path | None = None
    column_specs: "OrderedDict[str, ColumnSpec]" = field(
        default_factory=OrderedDict
    )
    column_order: list[str] = field(default_factory=list)
    visible_columns: list[str] = field(default_factory=list)
    grouping_accessors: "OrderedDict[str, Callable[[OperationRecord], object]]" = field(
        default_factory=OrderedDict
    )
    grouping_labels: "OrderedDict[str, str]" = field(default_factory=OrderedDict)
    filter_controls: "OrderedDict[str, FilterControl]" = field(
        default_factory=OrderedDict
    )


@dataclass
class ColumnSpec:
    """Describes a column displayable in the main table."""

    identifier: str
    label: str
    getter: Callable[[OperationRecord], str]
    anchor: str = "center"
    width: int = 140
    grouping_key: str | None = None
    source: str | None = None


@dataclass
class WelcomeWindowHandles:
    """Useful information for tests on the created window."""

    root: _TkRoot
    state: _AppState
    commands: Mapping[str, Callable[[], None]]


@dataclass
class FilterControl:
    """Dynamically configurable filter widget."""

    identifier: str
    label: str
    extractor: Callable[[OperationRecord], object]
    variable: object
    combobox: object
    default_label: str
    frame: object
    missing_label: str = "Not specified"

    def format_value(self, value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            normalized = value.strip()
            if normalized.lower() == "nan":
                return ""
            return normalized
        return str(value)

    def normalized_value(self, value: object) -> str:
        formatted = self.format_value(value)
        return formatted if formatted else self.missing_label


_MATERIAL_KEYWORDS = (
    "material",
    "alloy",
    "steel",
    "metal",
)


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    """Convert a hexadecimal color to an RGB tuple."""

    value = color.lstrip("#")
    if len(value) != 6:
        raise ValueError(f"Invalid color format: {color!r}")
    return (
        int(value[0:2], 16),
        int(value[2:4], 16),
        int(value[4:6], 16),
    )


def _rgb_to_hex(red: int, green: int, blue: int) -> str:
    """Return the hexadecimal representation of an RGB color."""

    red = max(0, min(255, red))
    green = max(0, min(255, green))
    blue = max(0, min(255, blue))
    return f"#{red:02x}{green:02x}{blue:02x}"


def _blend_colors(start: str, end: str, ratio: float) -> str:
    """Blend two hexadecimal colors returning an intermediate shade."""

    ratio = max(0.0, min(1.0, ratio))
    start_r, start_g, start_b = _hex_to_rgb(start)
    end_r, end_g, end_b = _hex_to_rgb(end)
    red = int(start_r + (end_r - start_r) * ratio)
    green = int(start_g + (end_g - start_g) * ratio)
    blue = int(start_b + (end_b - start_b) * ratio)
    return _rgb_to_hex(red, green, blue)


def _infer_process_family(record: OperationRecord) -> str:
    """Classify the operation into typical metalworking families."""

    tokens = "{} {}".format(record.process_type or "", record.process or "").lower()
    if any(keyword in tokens for keyword in ("cut", "laser", "plasma", "trim")):
        return "Cutting & trimming"
    if any(keyword in tokens for keyword in ("bend", "press", "roll", "stamp")):
        return "Bending & forming"
    if any(keyword in tokens for keyword in ("weld", "braze")):
        return "Welding"
    if any(keyword in tokens for keyword in ("assembl", "mount", "setup")):
        return "Assembly"
    if any(keyword in tokens for keyword in ("paint", "coating", "finish")):
        return "Surface finishing"
    if any(keyword in tokens for keyword in ("inspect", "test", "quality")):
        return "Quality control"
    return "Other process"


def _infer_material_family(record: OperationRecord) -> str:
    """Infer the processed material from extra columns when available."""

    for key in _MATERIAL_KEYWORDS:
        value = record.extra.get(key)
        if not value:
            continue
        text = str(value).strip().lower()
        if not text or text == "nan":
            continue
        if any(token in text for token in ("inox", "aisi", "stainless")):
            return "Stainless steel"
        if any(token in text for token in ("steel", "iron", "carbon")):
            return "Carbon steels"
        if "alumin" in text:
            return "Aluminum"
        if any(token in text for token in ("copper", "brass")):
            return "Copper / Brass"
        if "cast iron" in text:
            return "Cast iron"
        return text.title()
    return "Material not specified"


def _infer_productivity_band(record: OperationRecord) -> str:
    """Group hourly productivity into performance bands."""

    throughput = record.productivity_per_hour
    if throughput >= 120:
        return "Top productivity (≥120 pcs/hour)"
    if throughput >= 80:
        return "High yield (80-119 pcs/hour)"
    if throughput >= 50:
        return "Average productivity (50-79 pcs/hour)"
    if throughput > 0:
        return "Needs optimization (<50 pcs/hour)"
    return "No production"


def _combine_process_and_machine(record: OperationRecord) -> str:
    """Combine process and machine to analyze plant load."""

    process = record.process or "-"
    machine = record.machine or "-"
    return f"{process} • {machine}"


def _load_toolkit() -> _Toolkit:
    try:
        import tkinter as tk  # type: ignore
        from tkinter import filedialog, messagebox, ttk  # type: ignore
    except ModuleNotFoundError as exc:
        raise GUIUnavailableError(
            "Tkinter is not available in this environment: install the Windows graphical runtime."
        ) from exc
    except Exception as exc:  # pragma: no cover - unexpected path
        raise GUIUnavailableError("Unable to initialize Tkinter.") from exc

    return _Toolkit(tk=tk, ttk=ttk, messagebox=messagebox, filedialog=filedialog)


def launch_welcome_window(
    root_factory: Callable[[], _TkRoot] | None = None,
    *,
    run_mainloop: bool = True,
    operations_loader: Callable[[Path], list[OperationRecord]] | None = None,
    _toolkit: Dict[str, object] | None = None,
) -> WelcomeWindowHandles | None:
    """Show the main TruMetraPla graphical window."""

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
        except KeyError as exc:  # pragma: no cover - misuse of private parameter
            raise GUIUnavailableError("Incomplete graphics toolkit.") from exc

        if (
            toolkit.tk is None
            or toolkit.ttk is None
            or toolkit.messagebox is None
            or toolkit.filedialog is None
        ):
            raise GUIUnavailableError("Invalid graphics toolkit.")

    tk = toolkit.tk
    ttk = toolkit.ttk
    messagebox = toolkit.messagebox
    filedialog = toolkit.filedialog

    if root_factory is None:
        root: _TkRoot = tk.Tk()
    else:
        root = root_factory()

    root.title("TruMetraPla - Analytics Console")
    root.geometry("1080x680")
    try:
        root.minsize(920, 580)
    except Exception:  # pragma: no cover - some stubs may not implement minsize
        pass
    root.resizable(True, True)

    try:
        root.configure(background="#f4f6fb")
        root.option_add("*Font", "Segoe UI 10")
    except Exception:  # pragma: no cover - some test stubs do not implement configure
        pass

    style = None
    if hasattr(ttk, "Style"):
        try:
            style = ttk.Style()
        except Exception:  # pragma: no cover - some fake toolkits may fail
            style = None

    if style is not None:
        base_theme = "clam"
        app_theme = "TruMetraPla.light"

        def _safe_style_map(style_obj: object, style_name: str, **mapping: object) -> None:
            if hasattr(style_obj, "map"):
                getattr(style_obj, "map")(style_name, **mapping)

        try:
            style.theme_create(
                app_theme,
                parent=base_theme,
                settings={
                    "TFrame": {"configure": {"background": "#f4f6fb"}},
                    "TLabel": {
                        "configure": {
                            "background": "#f4f6fb",
                            "foreground": "#1f2937",
                            "font": ("Segoe UI", 10),
                        }
                    },
                    "TButton": {
                        "configure": {
                            "padding": (12, 8),
                            "borderwidth": 0,
                            "background": "#2563eb",
                            "foreground": "#ffffff",
                            "font": ("Segoe UI Semibold", 10),
                        }
                    },
                    "TCombobox": {
                        "configure": {
                            "fieldbackground": "#ffffff",
                            "background": "#ffffff",
                            "foreground": "#1f2937",
                            "padding": (8, 6),
                        }
                    },
                    "TScrollbar": {
                        "configure": {
                            "background": "#cbd5e1",
                            "troughcolor": "#f4f6fb",
                            "bordercolor": "#cbd5e1",
                            "arrowcolor": "#2563eb",
                        }
                    },
                },
            )
        except Exception:  # pragma: no cover - theme may already exist
            pass

        try:
            style.theme_use(app_theme)
        except Exception:  # pragma: no cover - theme not available
            try:
                style.theme_use(base_theme)
            except Exception:  # pragma: no cover - theme not available
                pass

        style.configure("Dashboard.TFrame", background="#f4f6fb")
        style.configure(
            "Card.TFrame",
            background="#ffffff",
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "Header.TLabel",
            background="#ffffff",
            foreground="#111827",
            font=("Segoe UI Semibold", 14),
        )
        style.configure(
            "Info.TLabel",
            background="#ffffff",
            foreground="#6b7280",
            font=("Segoe UI", 10),
        )
        style.configure(
            "Summary.TLabel",
            background="#ffffff",
            foreground="#374151",
            font=("Segoe UI", 10),
        )
        style.configure(
            "Status.TLabel",
            background="#f4f6fb",
            foreground="#2563eb",
            font=("Segoe UI", 9),
        )
        style.configure(
            "Credits.TLabel",
            background="#f4f6fb",
            foreground="#9ca3af",
            font=("Segoe UI", 9),
        )
        style.configure(
            "FilterLabel.TLabel",
            background="#f4f6fb",
            foreground="#374151",
            font=("Segoe UI Semibold", 9),
        )
        style.configure(
            "Accent.TButton",
            background="#2563eb",
            foreground="#ffffff",
            padding=(16, 8),
            font=("Segoe UI Semibold", 10),
        )
        style.configure(
            "Secondary.TButton",
            background="#e5e7eb",
            foreground="#1f2937",
            padding=(14, 8),
            font=("Segoe UI", 10),
        )
        _safe_style_map(
            style,
            "Accent.TButton",
            background=[("active", "#1d4ed8"), ("pressed", "#1e40af")],
            foreground=[("disabled", "#9ca3af")],
        )
        _safe_style_map(
            style,
            "Secondary.TButton",
            background=[("active", "#d1d5db"), ("pressed", "#cbd5e1")],
            foreground=[("disabled", "#9ca3af")],
        )
        _safe_style_map(
            style,
            "TCombobox",
            fieldbackground=[("readonly", "#ffffff")],
            background=[("readonly", "#ffffff")],
            foreground=[("readonly", "#1f2937")],
            selectbackground=[("readonly", "#2563eb")],
            selectforeground=[("readonly", "#ffffff")],
        )
        style.configure(
            "Treeview",
            background="#ffffff",
            fieldbackground="#ffffff",
            foreground="#1f2937",
            rowheight=28,
            bordercolor="#e5e7eb",
        )
        _safe_style_map(
            style,
            "Treeview",
            background=[("selected", "#dbeafe")],
            foreground=[("selected", "#1e3a8a")],
        )
        style.configure(
            "Treeview.Heading",
            background="#f1f5f9",
            foreground="#1f2937",
            relief="flat",
            font=("Segoe UI Semibold", 10),
        )
        _safe_style_map(
            style,
            "Treeview.Heading",
            background=[("active", "#e2e8f0")],
            foreground=[("pressed", "#2563eb")],
        )

    state = _AppState()
    loader = operations_loader or (lambda path: load_operations_from_excel(path))

    def _canonical_column_specs() -> OrderedDict[str, ColumnSpec]:
        specs: OrderedDict[str, ColumnSpec] = OrderedDict()
        specs["date"] = ColumnSpec(
            identifier="date",
            label="Date",
            getter=lambda record: record.date.strftime("%d/%m/%Y"),
            width=110,
            grouping_key="date",
        )
        specs["employee"] = ColumnSpec(
            identifier="employee",
            label="Employee",
            getter=lambda record: record.employee or "-",
            anchor="w",
            grouping_key="employee",
        )
        specs["process"] = ColumnSpec(
            identifier="process",
            label="Process",
            getter=lambda record: record.process or "-",
            anchor="w",
            grouping_key="process",
        )
        specs["process_type"] = ColumnSpec(
            identifier="process_type",
            label="Process type",
            getter=lambda record: record.process_type or "-",
            anchor="w",
            width=150,
            grouping_key="process_type",
        )
        specs["machine"] = ColumnSpec(
            identifier="machine",
            label="Machine",
            getter=lambda record: record.machine or "-",
            anchor="w",
            grouping_key="machine",
        )
        specs["quantity"] = ColumnSpec(
            identifier="quantity",
            label="Pieces",
            getter=lambda record: f"{record.quantity}",
            width=100,
        )
        specs["duration_minutes"] = ColumnSpec(
            identifier="duration_minutes",
            label="Duration (min)",
            getter=lambda record: f"{record.duration_minutes:.1f}",
            width=110,
        )
        specs["throughput"] = ColumnSpec(
            identifier="throughput",
            label="Pieces/hour",
            getter=lambda record: f"{record.productivity_per_hour:.2f}",
            width=110,
        )
        return specs

    state.column_specs = _canonical_column_specs()
    state.column_order = list(state.column_specs.keys())
    state.visible_columns = list(state.column_order)

    def _slugify_extra(label: str, used: set[str]) -> str:
        token = re.sub(r"[^0-9a-z]+", "_", label.lower()).strip("_")
        if not token:
            token = "column"
        base = f"extra_{token}"
        identifier = base
        counter = 1
        while identifier in used:
            identifier = f"{base}_{counter}"
            counter += 1
        used.add(identifier)
        return identifier

    def _refresh_column_specs(records: list[OperationRecord]) -> None:
        base_specs = _canonical_column_specs()
        used_ids = set(base_specs.keys())
        extras_order: list[str] = []
        for record in records:
            for key in record.extra.keys():
                if key not in extras_order:
                    extras_order.append(key)

        grouping_accessors: "OrderedDict[str, Callable[[OperationRecord], object]]" = (
            OrderedDict()
        )
        grouping_labels: "OrderedDict[str, str]" = OrderedDict()

        def _register_grouping(
            identifier: str,
            label: str,
            accessor: Callable[[OperationRecord], object],
        ) -> None:
            grouping_accessors[identifier] = accessor
            grouping_labels[identifier] = label

        _register_grouping("process", "Process", lambda record: record.process or "")
        _register_grouping("employee", "Employee", lambda record: record.employee or "")
        _register_grouping("machine", "Machine", lambda record: record.machine or "")
        _register_grouping(
            "process_type",
            "Process type",
            lambda record: record.process_type or "",
        )
        _register_grouping(
            "derived:process_machine",
            "Process and machine",
            _combine_process_and_machine,
        )
        _register_grouping(
            "derived:process_family",
            "Process family (metalworking)",
            _infer_process_family,
        )
        _register_grouping(
            "derived:productivity_band",
            "Productivity class (pieces/hour)",
            _infer_productivity_band,
        )
        _register_grouping(
            "derived:material_family",
            "Material processed",
            _infer_material_family,
        )

        specs: OrderedDict[str, ColumnSpec] = OrderedDict(base_specs)

        for column in extras_order:
            identifier = _slugify_extra(column, used_ids)
            grouping_key = f"extra:{column}"

            def _make_getter(field: str) -> Callable[[OperationRecord], str]:
                def _getter(record: OperationRecord, field: str = field) -> str:
                    value = record.extra.get(field, "")
                    if value in (None, "nan"):
                        return ""
                    return str(value)

                return _getter

            specs[identifier] = ColumnSpec(
                identifier=identifier,
                label=column,
                getter=_make_getter(column),
                anchor="w",
                width=max(140, min(len(column) * 10, 220)),
                grouping_key=grouping_key,
                source=column,
            )
            _register_grouping(
                grouping_key,
                column,
                lambda record, field=column: record.extra.get(field, ""),
            )

        state.column_specs = specs
        state.column_order = list(specs.keys())

        previous_selection = [
            column_id for column_id in state.visible_columns if column_id in specs
        ]
        if not previous_selection:
            previous_selection = list(base_specs.keys())
        for column_id in specs.keys():
            if column_id not in previous_selection:
                previous_selection.append(column_id)
        state.visible_columns = previous_selection
        state.grouping_accessors = grouping_accessors
        state.grouping_labels = grouping_labels

        active_filters = list(state.filter_controls.keys())
        for identifier in active_filters:
            if identifier not in grouping_accessors:
                control = state.filter_controls.pop(identifier)
                try:
                    control.frame.destroy()
                except Exception:  # pragma: no cover - widget already removed
                    pass

    # Textual state variables
    file_var = tk.StringVar(value="No file loaded")
    summary_var = tk.StringVar(
        value="Load an Excel file to activate the KPI dashboard"
    )
    status_var = tk.StringVar(value="System ready • No dataset loaded")

    # Main menu
    menubar = tk.Menu(root)
    file_menu = tk.Menu(menubar, tearoff=0)
    tools_menu = tk.Menu(menubar, tearoff=0)
    help_menu = tk.Menu(menubar, tearoff=0)

    def _active_columns() -> list[str]:
        selected = [
            column_id for column_id in state.visible_columns if column_id in state.column_specs
        ]
        if selected:
            return selected
        return list(state.column_specs.keys())

    def _configure_tree_columns() -> None:
        columns = _active_columns()
        tree.configure(columns=columns, displaycolumns=columns)
        for column_id in columns:
            spec = state.column_specs.get(column_id)
            if not spec:
                continue
            tree.heading(column_id, text=spec.label)
            tree.column(column_id, anchor=spec.anchor, width=spec.width)

    def _update_table(records: list[OperationRecord]) -> None:
        _configure_tree_columns()
        tree.delete(*tree.get_children())
        columns = _active_columns()
        for index, record in enumerate(records):
            values: list[str] = []
            for column_id in columns:
                spec = state.column_specs.get(column_id)
                if spec is None:
                    values.append("")
                    continue
                try:
                    value = spec.getter(record)
                except Exception:  # pragma: no cover - invalid custom getter
                    value = ""
                if not isinstance(value, str):
                    value = "" if value is None else str(value)
                values.append(value)

            tag = "evenrow" if index % 2 == 0 else "oddrow"
            tree.insert("", "end", values=tuple(values), tags=(tag,))

    def _format_summary(records: list[OperationRecord]) -> str:
        if not records:
            return "No data available"

        summary = summarize_operations(records)
        machines = len({record.machine for record in records if record.machine})
        process_types = len(
            {record.process_type for record in records if record.process_type}
        )
        return (
            "⟡ Total records: {records} • Quantity: {qty} • Hours: {hours:.2f} • "
            "Average throughput: {throughput:.2f} pieces/hour • Employees: {employees} • "
            "Processes: {processes} • Machines: {machines} • Process types: {process_types}"
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

    def _create_filter_control(
        identifier: str,
        label: str,
        *,
        accessor: Callable[[OperationRecord], object],
        default_label: str = "All",
        width: int = 24,
        missing_label: str = "Not specified",
    ) -> FilterControl:
        if identifier in state.filter_controls:
            return state.filter_controls[identifier]

        container = ttk.Frame(filters_frame, style="Dashboard.TFrame")
        container.pack(side="left", padx=(0, 12))

        ttk.Label(container, text=f"{label}:", style="FilterLabel.TLabel").pack(
            anchor="w"
        )

        variable = tk.StringVar(value=default_label)
        combobox = ttk.Combobox(
            container,
            width=width,
            state="readonly",
            textvariable=variable,
        )
        combobox.pack()
        combobox.configure(values=[default_label])
        combobox.current(0)

        control = FilterControl(
            identifier=identifier,
            label=label,
            extractor=accessor,
            variable=variable,
            combobox=combobox,
            default_label=default_label,
            frame=container,
            missing_label=missing_label,
        )
        state.filter_controls[identifier] = control

        def _on_change(*_args: object) -> None:
            _apply_filters()

        combobox.bind("<<ComboboxSelected>>", _on_change)
        return control

    def _populate_filter_control(
        control: FilterControl, records: list[OperationRecord]
    ) -> None:
        if not records:
            control.combobox.configure(values=[control.default_label])
            control.variable.set(control.default_label)
            return

        values_set = {
            control.normalized_value(control.extractor(record)) for record in records
        }

        sorted_values = sorted(
            value
            for value in values_set
            if value not in {control.default_label, control.missing_label}
        )
        if control.missing_label in values_set:
            sorted_values.append(control.missing_label)

        options = [control.default_label] + sorted_values if sorted_values else [
            control.default_label
        ]
        control.combobox.configure(values=options)
        control.variable.set(control.default_label)

    def _available_filter_fields() -> list[tuple[str, str]]:
        return [
            (identifier, label)
            for identifier, label in state.grouping_labels.items()
            if identifier not in state.filter_controls
        ]

    def _prompt_add_filter() -> None:
        available = _available_filter_fields()
        if not available:
            messagebox.showinfo(
                "No fields available",
                "All filterable fields have already been added.",
            )
            return

        dialog = tk.Toplevel(root)
        dialog.title("Add filter")
        dialog.geometry("320x160")
        dialog.transient(root)

        container = ttk.Frame(dialog, padding=16)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text="Select the field to add to the filters.",
            justify="left",
        ).pack(anchor="w", pady=(0, 12))

        labels = [label for _identifier, label in available]
        mapping = {label: identifier for identifier, label in available}
        selection_var = tk.StringVar(value=labels[0])

        combo = ttk.Combobox(
            container,
            state="readonly",
            values=labels,
            textvariable=selection_var,
        )
        combo.pack(fill="x")
        combo.current(0)

        feedback_var = tk.StringVar(value="")
        ttk.Label(container, textvariable=feedback_var, foreground="#d97706").pack(
            anchor="w", pady=(8, 0)
        )

        def _confirm() -> None:
            label = selection_var.get()
            identifier = mapping.get(label)
            if not identifier:
                feedback_var.set("Select a valid field.")
                return

            accessor = state.grouping_accessors.get(identifier)
            if accessor is None:
                feedback_var.set(
                    "The selected field is not available in this analysis."
                )
                return

            control = _create_filter_control(
                identifier,
                label,
                accessor=accessor,
                default_label="All",
            )
            if state.records:
                _populate_filter_control(control, state.records)
            dialog.destroy()

        actions = ttk.Frame(container)
        actions.pack(fill="x", pady=(16, 0))

        ttk.Button(actions, text="Cancel", command=dialog.destroy).pack(
            side="right", padx=(0, 8)
        )
        ttk.Button(actions, text="Add", command=_confirm).pack(side="right")

        try:
            dialog.grab_set()
        except Exception:  # pragma: no cover - headless environments
            pass
        dialog.focus_force()
        if hasattr(root, "wait_window"):
            root.wait_window(dialog)
        else:  # pragma: no cover
            dialog.mainloop()

    def _apply_filters() -> None:
        if not state.records:
            summary_var.set(
                "No data to filter • import an Excel file to start."
            )
            status_var.set("Filters pending • Waiting for data")
            tree.delete(*tree.get_children())
            return

        active_filters = [
            control
            for control in state.filter_controls.values()
            if control.variable.get() not in {"", control.default_label}
        ]

        filtered: list[OperationRecord] = []
        for record in state.records:
            include = True
            for control in active_filters:
                expected = control.variable.get()
                record_value = control.normalized_value(control.extractor(record))
                if record_value != expected:
                    include = False
                    break
            if include:
                filtered.append(record)

        state.filtered_records = filtered
        _update_table(filtered)
        summary_var.set(_format_summary(filtered))
        status_var.set(
            "Active filters • {visible}/{total} records visible".format(
                visible=len(filtered), total=len(state.records)
            )
        )

    def _refresh_filters(records: list[OperationRecord]) -> None:
        for control in state.filter_controls.values():
            _populate_filter_control(control, records)
        state.filtered_records = records

    def _prompt_column_mapping(excel_path: Path) -> dict[str, str] | None:
        try:
            import pandas as pd
        except ModuleNotFoundError as exc:  # pragma: no cover - required dependency
            messagebox.showerror(
                "Pandas not available",
                "Install the 'pandas' dependency to import Excel files.",
            )
            raise GUIUnavailableError("Pandas required for Excel file handling") from exc

        try:
            preview = pd.read_excel(excel_path, sheet_name=0, nrows=25)
        except Exception as exc:  # pragma: no cover - unexpected I/O errors
            messagebox.showerror(
                "Read error",
                f"Unable to read file headers: {exc}",
            )
            return None

        columns = list(preview.columns)
        if not columns:
            messagebox.showerror(
                "Missing headers",
                "The selected Excel file contains no column headers.",
            )
            return None

        column_samples = {
            column: preview[column].dropna().astype(str).head(12).tolist()
            for column in columns
        }
        suggestions, _missing = suggest_column_mapping(
            columns, column_samples=column_samples
        )
        option_values = ["(Select)"] + columns

        field_labels: dict[str, str] = {
            "date": "Date (required)",
            "employee": "Employee",
            "process": "Process",
            "quantity": "Quantity produced",
            "duration_minutes": "Duration in minutes",
        }

        dialog = tk.Toplevel(root)
        dialog.title("Map Excel columns")
        dialog.geometry("480x360")
        dialog.transient(root)

        container = ttk.Frame(dialog, padding=16)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text=(
                "Match the required fields to the Excel file columns."
                " Selections will be saved for this import."
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
                values = ["(Optional)"] + columns
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
                if field in optional_fields and value == "(Optional)":
                    continue
                if value == "(Select)":
                    feedback_var.set("Complete the selection of all required columns.")
                    return
                if value in used_columns:
                    feedback_var.set(
                        "Each column can be assigned to only one field. Review the selection."
                    )
                    return
                used_columns.add(value)
                selections[field] = value

            result = selections
            dialog.destroy()

        def _cancel() -> None:
            result = None
            dialog.destroy()

        ttk.Button(actions, text="Cancel", command=_cancel).pack(side="right", padx=(0, 8))
        ttk.Button(actions, text="OK", command=_confirm).pack(side="right")

        try:
            dialog.grab_set()
        except Exception:  # pragma: no cover - some headless environments
            pass
        dialog.focus_force()

        if hasattr(root, "wait_window"):
            root.wait_window(dialog)
        else:  # pragma: no cover - fallback for test stubs
            dialog.mainloop()

        return result

    def _open_file() -> None:
        path_str = filedialog.askopenfilename(
            title="Select an Excel file",
            filetypes=(
                ("Excel files", "*.xlsx *.xlsm *.xls *.xlsb"),
                ("All files", "*.*"),
            ),
        )

        if not path_str:
            return

        excel_path = Path(path_str)

        try:
            records = loader(excel_path)
        except FileNotFoundError:
            messagebox.showerror("File not found", f"The file {excel_path} does not exist.")
            return
        except ColumnMappingError:
            mapping = _prompt_column_mapping(excel_path)
            if not mapping:
                status_var.set("Import cancelled: map the required columns.")
                return
            try:
                records = load_operations_from_excel(excel_path, column_mapping=mapping)
            except ColumnMappingError as exc:
                messagebox.showerror("Missing columns", str(exc))
                return
            except Exception as exc:  # pragma: no cover - unexpected errors
                messagebox.showerror("Error", f"Unable to read the file: {exc}")
                return
        except Exception as exc:  # pragma: no cover - unexpected errors
            messagebox.showerror("Error", f"Unable to read the file: {exc}")
            return

        state.records = records
        state.file_path = excel_path
        file_var.set(f"Current file: {excel_path}")
        status_var.set(f"Active dataset • {len(records)} records loaded")
        _refresh_column_specs(records)
        _refresh_filters(records)
        _apply_filters()

    def _open_column_manager() -> None:
        if not state.column_specs:
            messagebox.showinfo(
                "Columns not available",
                "Load an Excel file to customize the table.",
            )
            return

        dialog = tk.Toplevel(root)
        dialog.title("Configure visible columns")
        dialog.geometry("360x420")
        dialog.transient(root)
        try:
            dialog.configure(background="#f4f6fb")
        except Exception:  # pragma: no cover - test stubs
            pass

        container = ttk.Frame(dialog, padding=16, style="Card.TFrame")
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text="Select the columns to show in the main table.",
            wraplength=320,
            justify="left",
            style="Info.TLabel",
        ).pack(fill="x", pady=(0, 12))

        checklist = ttk.Frame(container, style="Card.TFrame")
        checklist.pack(fill="both", expand=True)

        bool_vars: dict[str, object] = {}
        for column_id in state.column_order:
            spec = state.column_specs[column_id]
            var = tk.BooleanVar(value=column_id in _active_columns())
            bool_vars[column_id] = var
            ttk.Checkbutton(
                checklist,
                text=spec.label,
                variable=var,
            ).pack(anchor="w", pady=2)

        feedback_var = tk.StringVar(value="")
        ttk.Label(
            checklist,
            textvariable=feedback_var,
            foreground="#f97316",
            style="Info.TLabel",
        ).pack(anchor="w", pady=(8, 0))

        actions = ttk.Frame(container, style="Card.TFrame")
        actions.pack(fill="x", pady=(18, 0))

        def _confirm_columns() -> None:
            selected = [
                column_id for column_id, var in bool_vars.items() if bool(var.get())
            ]
            if not selected:
                feedback_var.set("Select at least one column to display.")
                return

            state.visible_columns = selected
            current = state.filtered_records or state.records
            _update_table(current)
            status_var.set(
                "Columns updated ({})".format(
                    ", ".join(state.column_specs[col].label for col in selected)
                )
            )
            dialog.destroy()

        ttk.Button(actions, text="Cancel", command=dialog.destroy).pack(
            side="right", padx=(0, 8)
        )
        ttk.Button(actions, text="Apply", command=_confirm_columns).pack(side="right")

        try:
            dialog.grab_set()
        except Exception:  # pragma: no cover - headless environments
            pass
        dialog.focus_force()
        if hasattr(root, "wait_window"):
            root.wait_window(dialog)
        else:  # pragma: no cover
            dialog.mainloop()

    def _show_kpi_dialog() -> None:
        if not state.filtered_records:
            messagebox.showinfo(
                "No data",
                "Load an Excel file and apply filters to view KPIs.",
            )
            return

        summary = summarize_operations(state.filtered_records)
        top_employees = group_by_employee(state.filtered_records)[:3]
        top_processes = group_by_process(state.filtered_records)[:3]

        def _format_entities(entities: list) -> str:
            if not entities:
                return "None"
            return "\n".join(
                f"- {item.entity}: {item.total_quantity} pieces ({item.throughput:.2f} pcs/hour)"
                for item in entities
            )

        message = (
            "Total quantity: {qty}\n"
            "Total hours: {hours:.2f}\n"
            "Average throughput: {throughput:.2f} pieces/hour\n"
            "Unique employees: {employees}\n"
            "Processes monitored: {processes}\n\n"
            "Top employees:\n{top_employees}\n\n"
            "Top processes:\n{top_processes}"
        ).format(
            qty=summary.total_quantity,
            hours=summary.total_hours,
            throughput=summary.throughput,
            employees=summary.employees,
            processes=summary.processes,
            top_employees=_format_entities(top_employees),
            top_processes=_format_entities(top_processes),
        )

        messagebox.showinfo("Key KPIs", message)

    def _show_pie_chart() -> None:
        records = state.filtered_records or state.records
        if not records:
            messagebox.showinfo(
                "No data",
                "Load an Excel file and apply filters to generate the chart.",
            )
            return

        try:
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure
        except ModuleNotFoundError:  # pragma: no cover - optional dependency
            messagebox.showerror(
                "Matplotlib not available",
                "Install the optional 'matplotlib' dependency to view charts.",
            )
            return
        except Exception as exc:  # pragma: no cover - unexpected errors
            messagebox.showerror(
                "Chart error",
                f"Unable to initialize the chart engine: {exc}",
            )
            return

        chart_window = tk.Toplevel(root)
        chart_window.title("TruMetraPla Chart Report")
        chart_window.geometry("720x520")
        try:
            chart_window.minsize(560, 420)
        except Exception:  # pragma: no cover - some stubs do not implement minsize
            pass

        container = ttk.Frame(chart_window, padding=16)
        container.pack(fill="both", expand=True)

        heading = ttk.Label(
            container,
            text="Production quantity distribution",
            font=("Segoe UI", 12, "bold"),
        )
        heading.pack(anchor="w")

        options_frame = ttk.Frame(container)
        options_frame.pack(fill="x", pady=(12, 8))

        ttk.Label(options_frame, text="Group by:").pack(side="left")

        grouping_items = list(state.grouping_labels.items()) or [
            ("process", "Process"),
            ("employee", "Employee"),
        ]
        grouping_labels = [label for _identifier, label in grouping_items]
        grouping_lookup = {label: identifier for identifier, label in grouping_items}

        grouping_combo = ttk.Combobox(
            options_frame,
            state="readonly",
            values=grouping_labels,
            width=32,
        )
        grouping_combo.current(0)
        grouping_combo.pack(side="left", padx=8)

        figure = Figure(figsize=(5.8, 4.2), dpi=100)
        axis = figure.add_subplot(111)
        canvas = FigureCanvasTkAgg(figure, master=container)
        canvas.get_tk_widget().pack(fill="both", expand=True)

        export_frame = ttk.Frame(container)
        export_frame.pack(fill="x", pady=(6, 0))

        def _export_chart(fmt: str) -> None:
            default_name = f"production-chart.{fmt}"
            if fmt == "pdf":
                filetypes = [("PDF document", "*.pdf")]
            else:
                filetypes = [("JPEG image", "*.jpg;*.jpeg"), ("All files", "*.*")]
            path = filedialog.asksaveasfilename(
                title="Export chart",
                defaultextension=f".{fmt}",
                filetypes=filetypes,
                initialfile=default_name,
            )
            if not path:
                return
            try:
                save_format = "jpeg" if fmt == "jpg" else fmt
                figure.savefig(path, format=save_format, bbox_inches="tight")
                info_var.set(f"Chart exported to {path}")
            except Exception as exc:  # pragma: no cover - disk write errors
                messagebox.showerror(
                    "Export error",
                    f"Unable to save the chart: {exc}",
                )

        ttk.Button(
            export_frame,
            text="Save PDF",
            command=lambda: _export_chart("pdf"),
        ).pack(side="right", padx=4)
        ttk.Button(
            export_frame,
            text="Save JPG",
            command=lambda: _export_chart("jpg"),
        ).pack(side="right", padx=4)

        info_var = tk.StringVar(value="")
        ttk.Label(container, textvariable=info_var, wraplength=660, justify="center").pack(
            fill="x", pady=(8, 0)
        )

        def _normalize_group_value(value: object) -> str:
            if value is None:
                return "Not specified"
            if isinstance(value, str):
                text = value.strip()
                return text if text else "Not specified"
            return str(value)

        def _build_breakdown(identifier: str) -> list[tuple[str, int]]:
            accessor = state.grouping_accessors.get(identifier)
            if accessor is None:
                return []
            totals: dict[str, int] = defaultdict(int)
            for record in records:
                label = _normalize_group_value(accessor(record))
                totals[label] += record.quantity
            breakdown = [
                (label, quantity)
                for label, quantity in totals.items()
                if quantity > 0
            ]
            breakdown.sort(key=lambda item: item[1], reverse=True)
            return breakdown

        def _refresh_chart(*_args: object) -> None:
            selected_label = grouping_combo.get()
            identifier = grouping_lookup.get(selected_label, "process")
            breakdown = _build_breakdown(identifier)
            if not breakdown:
                info_var.set(
                    "No data with positive quantities available for the selected chart."
                )
                axis.clear()
                canvas.draw_idle()
                return

            info_var.set("")
            axis.clear()

            values = [quantity for _label, quantity in breakdown]
            labels = [label for label, _quantity in breakdown]
            total = sum(values)

            def _format_pct(pct: float) -> str:
                absolute = int(round(pct * total / 100.0))
                return f"{pct:.1f}% ({absolute} pieces)"

            axis.pie(
                values,
                labels=labels,
                autopct=_format_pct,
                startangle=90,
            )
            axis.set_title(f"Quantity distribution by {selected_label.lower()}")
            axis.axis("equal")
            canvas.draw_idle()

        grouping_combo.bind("<<ComboboxSelected>>", _refresh_chart)
        _refresh_chart()

    # Build the main layout
    menubar.add_cascade(label="File", menu=file_menu)
    menubar.add_cascade(label="Tools", menu=tools_menu)
    menubar.add_cascade(label="Help", menu=help_menu)

    file_menu.add_command(label="Open Excel file...", command=_open_file)
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=root.destroy)

    tools_menu.add_command(label="Add filter", command=_prompt_add_filter)
    tools_menu.add_command(label="Configure columns", command=_open_column_manager)
    tools_menu.add_separator()
    tools_menu.add_command(label="Show KPIs", command=_show_kpi_dialog)
    tools_menu.add_command(label="Show chart", command=_show_pie_chart)

    help_menu.add_command(
        label="About",
        command=lambda: messagebox.showinfo(
            "About TruMetraPla",
            "TruMetraPla - Industrial productivity analysis tool.\n\n"
            "Analyze Excel production data, generate KPIs, and prepare professional reports.",
        ),
    )

    try:
        root.config(menu=menubar)
    except Exception:  # pragma: no cover - some test stubs do not implement config
        pass

    # Header
    header = ttk.Frame(root, style="Dashboard.TFrame")
    header.pack(fill="x", padx=16, pady=(16, 8))

    ttk.Label(
        header,
        text="TruMetraPla",
        style="Header.TLabel",
    ).pack(side="left")

    ttk.Label(
        header,
        textvariable=file_var,
        style="Info.TLabel",
    ).pack(side="right")

    # Filters bar
    filters_frame = ttk.Frame(root, style="Dashboard.TFrame")
    filters_frame.pack(fill="x", padx=16, pady=(0, 8))

    # Summary bar
    summary_bar = ttk.Frame(root, style="Card.TFrame")
    summary_bar.pack(fill="x", padx=16, pady=(0, 8))

    ttk.Label(
        summary_bar,
        textvariable=summary_var,
        style="Summary.TLabel",
        wraplength=1000,
    ).pack(fill="x", padx=12, pady=10)

    # Table
    table_frame = ttk.Frame(root, style="Card.TFrame")
    table_frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))

    tree = ttk.Treeview(table_frame, show="headings")
    tree.pack(side="left", fill="both", expand=True)

    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    scrollbar.pack(side="right", fill="y")
    tree.configure(yscrollcommand=scrollbar.set)

    tree.tag_configure("evenrow", background="#ffffff")
    tree.tag_configure("oddrow", background="#f8fafc")

    # Status bar
    status_bar = ttk.Frame(root, style="Dashboard.TFrame")
    status_bar.pack(fill="x", padx=16, pady=(0, 12))

    ttk.Label(
        status_bar,
        textvariable=status_var,
        style="Status.TLabel",
    ).pack(side="left")

    ttk.Label(
        status_bar,
        text="TruMetraPla v1.0.0",
        style="Credits.TLabel",
    ).pack(side="right")

    if run_mainloop:
        root.mainloop()

    return WelcomeWindowHandles(
        root=root,
        state=state,
        commands={
            "open_file": _open_file,
            "add_filter": _prompt_add_filter,
            "configure_columns": _open_column_manager,
            "show_kpi": _show_kpi_dialog,
            "show_chart": _show_pie_chart,
        },
    )
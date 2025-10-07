import types
from datetime import date
from pathlib import Path

import pytest

from trumetrapla.gui import GUIUnavailableError, launch_welcome_window
from trumetrapla.models import OperationRecord


class DummyStringVar:
    def __init__(self, value: str = "") -> None:
        self._value = value

    def set(self, value: str) -> None:
        self._value = value

    def get(self) -> str:
        return self._value


class DummyBooleanVar:
    def __init__(self, value: bool = False) -> None:
        self._value = bool(value)

    def set(self, value: bool) -> None:
        self._value = bool(value)

    def get(self) -> bool:
        return self._value


class DummyMenu:
    def __init__(self, *_args, **_kwargs) -> None:
        self.items: list[tuple[str, tuple]] = []

    def add_command(self, label: str, command=None, **_kwargs) -> None:
        self.items.append(("command", (label, command)))

    def add_separator(self) -> None:
        self.items.append(("separator", tuple()))

    def add_cascade(self, label: str, menu) -> None:
        self.items.append(("cascade", (label, menu)))


class DummyRoot:
    def __init__(self, tk_module: "DummyTkModule") -> None:
        self.tk_module = tk_module
        self.title_value: str | None = None
        self.geometry_value: str | None = None
        self.minsize_value: tuple[int, int] | None = None
        self.resizable_value: tuple[bool, bool] | None = None
        self.configure_calls: list[dict[str, object]] = []
        self.config_calls: list[dict[str, object]] = []
        self.mainloop_called = False

    def title(self, value: str) -> None:
        self.title_value = value

    def geometry(self, value: str) -> None:
        self.geometry_value = value

    def minsize(self, width: int, height: int) -> None:
        self.minsize_value = (width, height)

    def resizable(self, width: bool, height: bool) -> None:
        self.resizable_value = (width, height)

    def configure(self, **kwargs: object) -> None:
        self.configure_calls.append(kwargs)

    def config(self, **kwargs: object) -> None:
        self.config_calls.append(kwargs)

    def destroy(self) -> None:  # pragma: no cover - richiamato dai pulsanti
        pass

    def mainloop(self) -> None:
        self.mainloop_called = True


class DummyWidget:
    def __init__(self, *args, **kwargs) -> None:
        self.kwargs = kwargs
        self.pack_calls: list[dict[str, object]] = []
        self.configure_calls: list[dict[str, object]] = []
        self.bind_calls: list[tuple[str, object]] = []

    def pack(self, **kwargs) -> None:
        self.pack_calls.append(kwargs)

    def configure(self, **kwargs) -> None:
        self.configure_calls.append(kwargs)

    def bind(self, event: str, callback) -> None:
        self.bind_calls.append((event, callback))


class DummyButton(DummyWidget):
    def __init__(self, *args, command=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.command = command


class DummyCheckbutton(DummyWidget):
    def __init__(self, *args, variable=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.variable = variable


class DummyLabel(DummyWidget):
    instances: list["DummyLabel"] = []

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        DummyLabel.instances.append(self)


class DummyCombobox(DummyWidget):
    def __init__(self, *args, textvariable=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.values: list[str] = []
        self.textvariable = textvariable or DummyStringVar()
        self.current_index: int = 0

    def configure(self, **kwargs) -> None:  # type: ignore[override]
        super().configure(**kwargs)
        if "values" in kwargs:
            self.values = list(kwargs["values"])

    def current(self, index: int) -> None:
        self.current_index = index
        if self.values:
            self.textvariable.set(self.values[index])

    def get(self) -> str:
        return self.textvariable.get()


class DummyTreeview(DummyWidget):
    def __init__(self, *args, columns=(), **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.columns = columns
        self.headings: dict[str, str] = {}
        self.column_options: dict[str, dict[str, object]] = {}
        self.items: dict[str, tuple] = {}
        self._next_id = 0
        self.yscroll = None
        self.xscroll = None

    def heading(self, column: str, text: str) -> None:
        self.headings[column] = text

    def column(self, column: str, **kwargs) -> None:
        self.column_options[column] = kwargs

    def insert(self, *_args, values=(), **_kwargs) -> str:
        identifier = f"I{self._next_id}"
        self._next_id += 1
        self.items[identifier] = values
        return identifier

    def get_children(self) -> list[str]:
        return list(self.items.keys())

    def delete(self, *item_ids: str) -> None:
        if not item_ids:
            self.items.clear()
        for item_id in item_ids:
            self.items.pop(item_id, None)

    def configure(self, **kwargs) -> None:  # type: ignore[override]
        super().configure(**kwargs)
        if "yscrollcommand" in kwargs:
            self.yscroll = kwargs["yscrollcommand"]
        if "xscrollcommand" in kwargs:
            self.xscroll = kwargs["xscrollcommand"]

    def yview(self, *args, **kwargs) -> tuple:
        return args  # pragma: no cover - utilizzato solo come callback

    def xview(self, *args, **kwargs) -> tuple:
        return args  # pragma: no cover - utilizzato solo come callback


class DummyScrollbar(DummyWidget):
    def __init__(self, *args, command=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.command = command
        self.set_calls: list[tuple[object, object]] = []

    def set(self, first, last) -> None:
        self.set_calls.append((first, last))


class DummyStyle:
    def __init__(self) -> None:
        self.theme: str | None = None
        self.configure_calls: list[tuple[str, dict[str, object]]] = []
        self.map_calls: list[tuple[str, dict[str, object]]] = []

    def theme_use(self, theme: str) -> None:
        self.theme = theme

    def configure(self, style_name: str, **kwargs) -> None:
        self.configure_calls.append((style_name, kwargs))

    def map(self, style_name: str, **kwargs) -> None:
        self.map_calls.append((style_name, kwargs))


class DummyMessagebox:
    def __init__(self) -> None:
        self.info_calls: list[tuple[str, str]] = []
        self.error_calls: list[tuple[str, str]] = []

    def showinfo(self, title: str, message: str) -> None:
        self.info_calls.append((title, message))

    def showerror(self, title: str, message: str) -> None:
        self.error_calls.append((title, message))


class DummyFileDialog:
    def __init__(self) -> None:
        self.return_value: str = ""
        self.calls: list[dict[str, object]] = []

    def askopenfilename(self, **kwargs) -> str:
        self.calls.append(kwargs)
        return self.return_value


class DummyTkModule:
    def __init__(self) -> None:
        self.instances: list[DummyRoot] = []
        self.Menu = DummyMenu
        self.StringVar = DummyStringVar
        self.BooleanVar = DummyBooleanVar

    def Tk(self) -> DummyRoot:
        root = DummyRoot(self)
        self.instances.append(root)
        return root


class DummyToolkit(dict):
    def __init__(self) -> None:
        DummyLabel.instances = []
        self.tk_module = DummyTkModule()
        self.messagebox = DummyMessagebox()
        self.filedialog = DummyFileDialog()
        self.ttk_module = types.SimpleNamespace(
            Frame=DummyWidget,
            Label=DummyLabel,
            Button=DummyButton,
            Combobox=DummyCombobox,
            Treeview=DummyTreeview,
            Scrollbar=DummyScrollbar,
            Checkbutton=DummyCheckbutton,
            Style=DummyStyle,
        )
        super().__init__(
            tk=self.tk_module,
            ttk=self.ttk_module,
            messagebox=self.messagebox,
            filedialog=self.filedialog,
        )


def test_launch_welcome_window_loads_excel_and_updates_state():
    toolkit = DummyToolkit()
    sample_records = [
        OperationRecord(
            date=date(2024, 1, 1),
            employee="Anna",
            process="Taglio",
            machine="Laser 1",
            process_type="Taglio",
            quantity=10,
            duration_minutes=60,
        ),
        OperationRecord(
            date=date(2024, 1, 2),
            employee="Luca",
            process="Assemblaggio",
            machine="Linea 3",
            process_type="Assemblaggio",
            quantity=8,
            duration_minutes=90,
        ),
    ]

    loader_calls: dict[str, Path] = {}

    def fake_loader(path: Path) -> list[OperationRecord]:
        loader_calls["path"] = path
        return sample_records

    toolkit.filedialog.return_value = "C:/dati.xlsx"

    handles = launch_welcome_window(
        run_mainloop=False,
        operations_loader=fake_loader,
        _toolkit=toolkit,
    )

    assert handles is not None
    root = handles.root
    assert root.title_value == "TruMetraPla - Console Analitica"
    assert root.resizable_value == (True, True)

    assert any(
        widget.kwargs.get("text") == "Prodotto da Francesco Castaldi"
        for widget in DummyLabel.instances
    )

    handles.commands["open_file"]()

    assert loader_calls["path"] == Path("C:/dati.xlsx")
    assert handles.state.records == sample_records
    assert handles.state.filtered_records == sample_records
    assert toolkit.messagebox.error_calls == []


def test_extra_columns_are_registered_and_groupable():
    toolkit = DummyToolkit()
    sample_records = [
        OperationRecord(
            date=date(2024, 5, 1),
            employee="Anna",
            process="Taglio",
            machine="Laser 2",
            process_type="Taglio",
            quantity=20,
            duration_minutes=45,
            extra={"Turno": "Notte", "Note": "Urgente"},
        )
    ]

    def fake_loader(_: Path) -> list[OperationRecord]:
        return sample_records

    toolkit.filedialog.return_value = "C:/shift.xlsx"

    handles = launch_welcome_window(
        run_mainloop=False,
        operations_loader=fake_loader,
        _toolkit=toolkit,
    )

    assert handles is not None
    handles.commands["open_file"]()

    specs = list(handles.state.column_specs.values())
    labels = [spec.label for spec in specs]
    assert "Turno" in labels
    turno_spec = next(spec for spec in specs if spec.label == "Turno")
    assert turno_spec.identifier in handles.state.visible_columns
    assert turno_spec.grouping_key is not None
    assert turno_spec.grouping_key in handles.state.grouping_accessors


def test_launch_welcome_window_requires_valid_toolkit():
    with pytest.raises(GUIUnavailableError):
        launch_welcome_window(
            run_mainloop=False,
            _toolkit={"tk": None, "ttk": None, "messagebox": None, "filedialog": None},
        )

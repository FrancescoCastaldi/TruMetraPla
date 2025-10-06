"""Componenti dell'interfaccia grafica di TruMetraPla."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Protocol


class GUIUnavailableError(RuntimeError):
    """Errore sollevato quando non è possibile avviare la GUI."""


class _TkRoot(Protocol):
    def title(self, value: str) -> None: ...

    def geometry(self, value: str) -> None: ...

    def resizable(self, width: bool, height: bool) -> None: ...

    def configure(self, **kwargs: object) -> None: ...

    def mainloop(self) -> None: ...

    def destroy(self) -> None: ...


@dataclass
class _Toolkit:
    tk: object
    ttk: object
    messagebox: object


def _load_toolkit() -> _Toolkit:
    try:
        import tkinter as tk  # type: ignore
        from tkinter import messagebox, ttk  # type: ignore
    except ModuleNotFoundError as exc:
        raise GUIUnavailableError(
            "Tkinter non è disponibile in questo ambiente: installa il runtime grafico di Windows."
        ) from exc
    except Exception as exc:  # pragma: no cover - percorso imprevisto
        raise GUIUnavailableError("Impossibile inizializzare Tkinter.") from exc

    return _Toolkit(tk=tk, ttk=ttk, messagebox=messagebox)


def launch_welcome_window(
    root_factory: Callable[[], _TkRoot] | None = None,
    *,
    run_mainloop: bool = True,
    _toolkit: Dict[str, object] | None = None,
) -> None:
    """Mostra la finestra grafica di benvenuto di TruMetraPla."""

    if _toolkit is None:
        toolkit = _load_toolkit()
    else:
        try:
            toolkit = _Toolkit(
                tk=_toolkit["tk"],
                ttk=_toolkit["ttk"],
                messagebox=_toolkit["messagebox"],
            )
        except KeyError as exc:  # pragma: no cover - uso errato del parametro privato
            raise GUIUnavailableError("Toolkit grafico incompleto.") from exc

        if toolkit.tk is None or toolkit.ttk is None or toolkit.messagebox is None:
            raise GUIUnavailableError("Toolkit grafico non valido.")

    tk = toolkit.tk
    ttk = toolkit.ttk
    messagebox = toolkit.messagebox

    if root_factory is None:
        root: _TkRoot = tk.Tk()
    else:
        root = root_factory()

    root.title("TruMetraPla - Benvenuto")
    root.geometry("480x320")
    root.resizable(False, False)

    try:
        root.configure(background="#f4f5f7")
    except Exception:  # pragma: no cover - alcuni stub di test non implementano configure
        pass

    frame = ttk.Frame(root, padding=20)
    frame.pack(expand=True, fill="both")

    title_label = ttk.Label(
        frame,
        text="Benvenuto in TruMetraPla",
        font=("Segoe UI", 16, "bold"),
        justify="center",
    )
    title_label.pack(pady=(0, 12))

    description = (
        "Grazie per aver installato TruMetraPla su Windows.\n"
        "Genera KPI di produttività e report immediati partendo dai tuoi file Excel."
    )
    body_label = ttk.Label(frame, text=description, wraplength=420, justify="center")
    body_label.pack(pady=(0, 16))

    button_area = ttk.Frame(frame)
    button_area.pack(pady=(0, 20))

    def _open_docs() -> None:
        import webbrowser

        webbrowser.open(
            "https://github.com/FrancescoCastaldi/TruMetraPla#readme",
            new=2,
        )

    def _show_cli_hint() -> None:
        messagebox.showinfo(
            "Modalità avanzata",
            "Apri il Prompt dei comandi e digita `trumetrapla --no-interactive` per la CLI.",
        )

    docs_button = ttk.Button(button_area, text="Guida rapida", command=_open_docs)
    docs_button.pack(side="left", padx=6)

    cli_button = ttk.Button(button_area, text="Usa la CLI", command=_show_cli_hint)
    cli_button.pack(side="left", padx=6)

    close_button = ttk.Button(frame, text="Chiudi", command=root.destroy)
    close_button.pack()

    if run_mainloop:
        root.mainloop()

    return None

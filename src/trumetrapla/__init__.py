"""TruMetraPla - tools for analyzing production performance."""

from .data_loader import load_operations_from_excel
from .metrics import (
    daily_trend,
    group_by_employee,
    group_by_process,
    summarize_operations,
)
from .models import OperationRecord
from .packaging import (
    BuildError,
    build_linux_bundle,
    build_windows_executable,
    build_windows_installer,
)

__all__ = [
    "OperationRecord",
    "load_operations_from_excel",
    "summarize_operations",
    "group_by_employee",
    "group_by_process",
    "daily_trend",
    "BuildError",
    "build_linux_bundle",
    "build_windows_executable",
    "build_windows_installer",
]

__version__ = "1.0.0"
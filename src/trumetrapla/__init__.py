"""TruMetraPla - strumenti per analizzare le performance produttive."""

from .data_loader import load_operations_from_excel
from .metrics import (
    daily_trend,
    group_by_employee,
    group_by_process,
    summarize_operations,
)
from .models import OperationRecord

__all__ = [
    "OperationRecord",
    "load_operations_from_excel",
    "summarize_operations",
    "group_by_employee",
    "group_by_process",
    "daily_trend",
]

__version__ = "0.1.0"

# TruMetraPla

> **Industrial productivity analysis** - Desktop and CLI tool to monitor production data from Excel with KPIs, an interactive dashboard, and automated reports.

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey)

---

## Key features

- **Smart import** - Automatic recognition of Excel columns (Italian/English)
- **Modern dashboard** - Graphical interface with a minimal tech theme and dynamic filters
- **Real-time KPIs** - Pieces produced, hours worked, average productivity per employee/process
- **Interactive charts** - Pie charts for quick analysis
- **Cross-platform** - Windows executable + Linux package
- **Full CLI** - Command-line reports with advanced options

---

## Installation

### Requirements

- Python 3.11 or higher
- pip (Python package manager)

### Method 1: Install with pip (recommended)

Install directly from the GitHub repository:

```bash
pip install git+https://github.com/FrancescoCastaldi/TruMetraPla.git
```

### Method 2: Install from source

Clone the repository and install in development mode:

```bash
# Clone the repository
git clone https://github.com/FrancescoCastaldi/TruMetraPla.git
cd TruMetraPla

# Install with dependencies
pip install -e .[test]
```

### Method 3: Precompiled executable

**Windows:**
- Download `TruMetraPla_Setup.exe` or `TruMetraPla.exe` from the [Releases](https://github.com/FrancescoCastaldi/TruMetraPla/releases) section
- Run the installer or the portable executable
- No Python installation required

**Linux:**
- Download `TruMetraPla-linux.tar.gz` from the [Releases](https://github.com/FrancescoCastaldi/TruMetraPla/releases) section
- Extract and run the installation script:

```bash
tar xzf TruMetraPla-linux.tar.gz
cd TruMetraPla-linux/
sudo ./install.sh
```

### Verify the installation

After installation, verify everything works:

```bash
# Show version and help
trumetrapla --help

# Launch the dashboard
trumetrapla
```

## Quick start

### Installation

```bash
pip install -e .[test]
```

### Basic usage

```bash
# Open the interactive dashboard
trumetrapla

# Generate a report from the CLI
trumetrapla report production.xlsx

# Create the Linux package
trumetrapla build-linux
```

---

## Desktop dashboard

The GUI offers a complete experience for data analysis:

- **File loading** - Drag & drop or File → Open menu
- **Dynamic filters** - Filter by operator, process, machine
- **Interactive table** - View all KPIs with sortable columns
- **Charts** - Pie reports based on process/operator
- **Export** - Save filtered data to CSV

### Launch the dashboard

**From source:**

```bash
trumetrapla
```

**From the Windows executable:**

- Double-click `dist/TruMetraPla.exe`
- Or install with the automatic installer

---

## Build & distribution

### Windows executable (.exe)

```bash
# Generate with PyInstaller
trumetrapla build-exe

# Executable available in dist/
```

### Linux package (.tar.gz)

```bash
# Automatic build
trumetrapla build-linux

# Output: dist/TruMetraPla-linux.tar.gz
```

**Installation on Linux:**

```bash
tar xzf TruMetraPla-linux.tar.gz
cd TruMetraPla-linux/
./install.sh
```

---

## CLI

### Full report

```bash
trumetrapla report production.xlsx
```

### Advanced options

```bash
# Map a canonical field to a specific column
trumetrapla report production.xlsx --column employee "Team member"

# Add a custom alias for automatic column recognition
trumetrapla report production.xlsx --alias process "Stage"

# Analyze a specific sheet
trumetrapla report production.xlsx --sheet "January"
```

---

## Use as a library

```python
from trumetrapla.data_loader import load_operations_from_excel
from trumetrapla.metrics import summarize_operations

# Load data
operations = load_operations_from_excel("production.xlsx")

# Calculate KPIs
summary = summarize_operations(operations)

print(f"Total pieces: {summary.total_quantity}")
print(f"Hours worked: {summary.total_hours}")
print(f"Average productivity: {summary.throughput:.2f} pieces/hour")
```

---

## System requirements

- **Python:** 3.11+
- **Dependencies:** pandas, openpyxl, tkinter, ttkbootstrap
- **Operating system:** Windows 10+, Linux (Ubuntu 20.04+, Debian 11+)
- **Recommended RAM:** 2 GB minimum, 4 GB for large Excel files
- **Screen resolution:** Minimum 1280x720 for optimal dashboard viewing

---

## Column mapping

TruMetraPla automatically recognizes the following Excel columns:

| Italian | English | Type |
|---------|---------|------|
| Data / Giorno | Date / Day | Date |
| Operatore / Dipendente | Operator / Employee | Text |
| Processo / Reparto | Process / Department | Text |
| Macchina / Attrezzatura | Machine / Equipment | Text |
| Pezzi / Quantità | Pieces / Quantity | Number |
| Ore / Tempo | Hours / Time | Number |

**Note:** The system supports unmapped extra columns (they are preserved in the data but not used for KPIs).

---

## Development

### Environment setup

```bash
git clone https://github.com/FrancescoCastaldi/TruMetraPla.git
cd TruMetraPla
pip install -e .[test]
```

### Tests

```bash
pytest tests/
```

### Project structure

```
TruMetraPla/
├── src/trumetrapla/
│   ├── __main__.py      # CLI entry point
│   ├── cli.py           # Command-line interface
│   ├── data_loader.py   # Excel import
│   ├── gui.py           # Tkinter dashboard
│   ├── metrics.py       # KPI calculation
│   ├── models.py        # Data models
│   ├── packaging.py     # Build & distribution
│   └── welcome_app.py   # Graphical entry point
├── tests/               # Test suite
└── docs/                # Documentation
```

---

## Windows installation

### Option 1: Automatic installer

1. Download `TruMetraPla_Setup.exe` from the [Releases](https://github.com/FrancescoCastaldi/TruMetraPla/releases) section
2. Run the installer and follow the instructions
3. Launch TruMetraPla from the Start menu

### Option 2: Portable executable

1. Download the standalone `TruMetraPla.exe`
2. Run it directly (no installation required)

---

## Linux installation

### Ubuntu/Debian

```bash
wget https://github.com/FrancescoCastaldi/TruMetraPla/releases/latest/download/TruMetraPla-linux.tar.gz
tar xzf TruMetraPla-linux.tar.gz
cd TruMetraPla-linux/
sudo ./install.sh
```

---

## FAQ

**Q: How do I export the filtered data?**

A: In the graphical dashboard, apply the desired filters and click "Export CSV".

**Q: Where are the reports saved?**

A: CLI reports are printed to the screen. Use `> output.txt` to save them to a file.

**Q: My Excel file has English columns, will it work?**

A: Yes, the system automatically recognizes both Italian and English names.

**Q: Can I use the program without installing Python?**

A: Yes, use the Windows executable (.exe) or the precompiled Linux package.

---

## Useful links

- [Full documentation](docs/)
- [Issue tracker](https://github.com/FrancescoCastaldi/TruMetraPla/issues)
- [Wiki](https://github.com/FrancescoCastaldi/TruMetraPla/wiki)

---

## License

MIT License - See [LICENSE](LICENSE) for details.

---

## Recent changes

### v1.0.0

- Full English translation of the interface and codebase
- New "Tech Minimal" UI theme - clean and professional design
- Interactive charts
- Integrated CSV export
- Support for arbitrary Excel columns
- Improved data loading performance

---

<p align="center">
  <i>Built with Python for industrial productivity analysis</i>
</p>
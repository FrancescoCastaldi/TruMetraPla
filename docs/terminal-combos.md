# CLI combinations for data extraction

TruMetraPla opens the graphical interface when you run `trumetrapla` without arguments.
The combinations below allow you to start the command-line modes to generate text reports directly from the terminal.

## Start the interactive CLI

```bash
trumetrapla --cli
```

Shows the numbered menu to:
- [1] Generate guided Excel reports
- [2] Build the Windows executable (`build-exe`)
- [3] Create the NSIS installer (`build-installer`)
- [4] View automation scripts
- [5] Reopen the GUI from the command line

## Basic report from an Excel file

```bash
trumetrapla report "C:\\Path\\production.xlsx"
```

Reads the default sheet (index 0) and prints the productivity summary to the terminal.

## Specify the worksheet

```bash
trumetrapla report production.xlsx --sheet "Line 2"
trumetrapla report production.xlsx --sheet 3
```

Accepts either the name or the numeric index of the Excel sheet.

## Manually map columns

When headers don't follow the automatically recognized names, you can provide the mappings.

```bash
trumetrapla report production.xlsx \
  --column date "Day" \
  --column employee "Operator" \
  --column process "Department" \
  --column machine "Island" \
  --column process_type "Category" \
  --column quantity "Pieces produced" \
  --column duration_minutes "Time (min)"
```

Repeat `--column` for each canonical field. The `machine` and `process_type` fields are optional but can be included when you want them in reports.

## Add permanent aliases

Additional aliases allow the automatic recognition to understand new headers without remapping every time.

```bash
trumetrapla report production.xlsx \
  --alias machine "Work center" \
  --alias process_type "Cycle type"
```

You can combine `--alias` with other parameters (`--sheet`, `--column`).

## Run the CLI without the interactive menu

```bash
trumetrapla --no-interactive
```

Prints the main options without waiting for input. Useful in scripts when you want to quickly recall the available commands.

## Other terminal utilities

*Generate executable*
```bash
trumetrapla build-exe --dist dist --onefile
```

*Compile installer*
```bash
trumetrapla build-installer --dist dist --reuse-exe
```

These commands can be run as-is or via the interactive menu (`trumetrapla --cli`).
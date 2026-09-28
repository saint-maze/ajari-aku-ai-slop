# sysmon-cli

Cross-platform Python CLI system monitor and developer inspection tool.

`sysmon` provides quick, formatted insight into real-time system metrics (CPU utilization, RAM, swap, and disk partition stats), top resource-consuming active processes, and Git repository status, with both human-readable terminal output and structured JSON mode.

## Installation

```bash
pip install -e .
```

## Features & Usage

### 1. System Metrics Reporting
Inspect real-time CPU utilization, system RAM usage, and disk partition statistics formatted in human-readable units (GB/MB, percentage):

```bash
# Default human-readable terminal output
sysmon system

# Structured JSON output
sysmon system --json

# Custom CPU sampling interval (seconds)
sysmon system --interval 0.5

# Inspect specific disk partition
sysmon system --disk C:\
```

Running `sysmon` with no subcommand also defaults to the system metrics report:
```bash
sysmon
sysmon --json
```

### 2. Process Inspection
List top active processes ranked by resource consumption:

```bash
# Top 10 processes sorted by CPU (default)
sysmon process

# Top 5 processes sorted by memory
sysmon process --limit 5 --sort memory

# Output processes as structured JSON
sysmon process --limit 10 --json
```

### 3. Git Repository Inspection
Inspect current Git repository branch, clean/dirty status, uncommitted changes, and latest commit:

```bash
# Inspect current working directory Git status
sysmon git

# Inspect specific repository path
sysmon git --path /path/to/repo

# Output Git status as JSON
sysmon git --json
```

When run outside a Git repository, `sysmon git` exits with non-zero code (1) and provides an informative error message.

### 4. Combined Overview
Display system metrics, top 5 processes, and Git repository status in a single consolidated report:

```bash
sysmon all
sysmon all --json
```

### 5. Help & Documentation
Detailed documentation is available via `--help`:

```bash
sysmon --help
sysmon system --help
sysmon process --help
sysmon git --help
sysmon all --help
```

## Running Tests

Run the comprehensive automated test suite:

```bash
pytest
```
or via unittest:
```bash
python -m unittest discover tests
```

## aadddd on aje
```kalo gabisa env nya, tambah (venv gajalan karena ga as admin)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

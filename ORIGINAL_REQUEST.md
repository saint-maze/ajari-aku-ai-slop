# Original User Request

## 2026-09-28T01:50:05Z

<USER_REQUEST>
This is a single self-contained fix; keep it small and focused.
Build a cross-platform Python CLI system monitor and developer tool that inspects system health (CPU, memory, disk usage), active processes, and Git repository status with clean, formatted output.

Working directory: C:\Users\baim\teamwork_projects\sysmon_cli
Integrity mode: development

## Requirements

### R1. System Metrics Reporting
The CLI must provide commands to measure and display real-time CPU utilization, system RAM usage, and disk partition stats in human-readable units (GB/MB, percentage).

### R2. Process and Repository Inspection
The CLI must allow listing the top resource-consuming processes (sorted by CPU or memory) and inspecting the current Git repository status and branch, with graceful error handling when executed outside a Git repository.

### R3. Dual Output Modes
The CLI must support human-readable formatted terminal output by default and a structured JSON output mode (`--json`) suitable for scripting and automated pipelines.

### R4. Automated Test Suite & Packaging
The project must include a self-contained automated test suite covering command-line argument parsing, valid metric collection, JSON schema validity, and error handling.

## Acceptance Criteria

### Functional Verification
- [ ] Executing the CLI with `--help` displays clear documentation for all commands and options with exit code 0.
- [ ] Running the system metrics command outputs CPU %, RAM usage, and disk stats and exits with code 0.
- [ ] Running system inspection with `--json` outputs valid JSON containing numeric metrics for CPU, RAM, and disk.
- [ ] Process inspection subcommand successfully lists top N processes showing PID, process name, and resource usage.
- [ ] Git inspection command outputs branch name and clean/dirty status when inside a Git repo, and displays an informative error message with non-zero exit code (or handled message) when not in a Git repo.

### Quality & Reliability
- [ ] Automated test suite runs and passes with 100% success rate.
- [ ] Invalid flags or arguments display helpful error messages to stderr and exit with non-zero status codes.
</USER_REQUEST>
<ADDITIONAL_METADATA>
The current local time is: 2026-09-28T08:50:05+07:00.
</ADDITIONAL_METADATA>

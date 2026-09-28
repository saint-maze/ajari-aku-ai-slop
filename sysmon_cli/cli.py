"""Command-line interface for sysmon."""

import argparse
import math
import sys
from typing import List, Optional

from sysmon_cli import __version__
from sysmon_cli.formatters import (
    format_all_report,
    format_git_report,
    format_process_report,
    format_system_report,
    to_json,
)
from sysmon_cli.git_status import get_git_status
from sysmon_cli.process import get_top_processes
from sysmon_cli.system import get_system_health


def build_parser() -> argparse.ArgumentParser:
    """Construct the command-line argument parser."""
    common_parent = argparse.ArgumentParser(add_help=False)
    common_parent.add_argument(
        "--json",
        action="store_true",
        dest="json_mode",
        help="Output results in structured JSON format",
    )

    parser = argparse.ArgumentParser(
        prog="sysmon",
        description="Cross-platform CLI system monitor and developer inspection tool.",
        parents=[common_parent],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show program's version number and exit",
    )

    subparsers = parser.add_subparsers(
        title="Commands",
        dest="command",
        metavar="<command>",
        help="Available inspection commands",
    )

    # 1. System Metrics Command
    sys_parser = subparsers.add_parser(
        "system",
        aliases=["sys", "metrics"],
        parents=[common_parent],
        help="Measure and display real-time CPU, RAM, and disk partition stats",
        description="Display real-time CPU utilization, system RAM usage, and disk partition stats in human-readable or JSON format.",
    )
    sys_parser.add_argument(
        "--interval",
        type=float,
        default=0.2,
        help="Sampling interval in seconds for CPU utilization (default: 0.2)",
    )
    sys_parser.add_argument(
        "-d", "--disk",
        type=str,
        default=None,
        help="Specific directory/partition path to inspect disk usage for",
    )

    # 2. Process Inspection Command
    proc_parser = subparsers.add_parser(
        "process",
        aliases=["processes", "ps", "top"],
        parents=[common_parent],
        help="Inspect top resource-consuming active processes",
        description="List top active processes sorted by CPU or memory consumption with PID and resource usage.",
    )
    proc_parser.add_argument(
        "-n", "--limit",
        type=int,
        default=10,
        help="Number of top processes to display (default: 10)",
    )
    proc_parser.add_argument(
        "-s", "--sort",
        choices=["cpu", "memory", "mem"],
        default="cpu",
        help="Sort processes by resource usage: 'cpu' or 'memory' (default: cpu)",
    )
    proc_parser.add_argument(
        "--interval",
        type=float,
        default=0.1,
        help="Sampling interval in seconds for CPU measurement (default: 0.1)",
    )
    proc_parser.add_argument(
        "--include-idle",
        action="store_true",
        help="Include Windows System Idle Process (PID 0) in ranking",
    )

    # 3. Git Repository Inspection Command
    git_parser = subparsers.add_parser(
        "git",
        aliases=["repo"],
        parents=[common_parent],
        help="Inspect current Git repository status and branch",
        description="Inspect Git repository status, active branch, commit info, and clean/dirty status.",
    )
    git_parser.add_argument(
        "-p", "--path",
        type=str,
        default=".",
        help="Target directory to inspect for Git repository (default: current directory)",
    )

    # 4. Combined 'all' Command
    all_parser = subparsers.add_parser(
        "all",
        aliases=["summary", "overview"],
        parents=[common_parent],
        help="Inspect system health, top processes, and Git status in one view",
        description="Run system metrics, top process ranking, and Git repository inspection together.",
    )
    all_parser.add_argument(
        "-n", "--limit",
        type=int,
        default=5,
        help="Number of top processes to include in summary (default: 5)",
    )
    all_parser.add_argument(
        "-s", "--sort",
        choices=["cpu", "memory", "mem"],
        default="cpu",
        help="Sort criteria for processes (default: cpu)",
    )
    all_parser.add_argument(
        "-p", "--path",
        type=str,
        default=".",
        help="Git repository path to inspect (default: current directory)",
    )
    all_parser.add_argument(
        "--interval",
        type=float,
        default=0.2,
        help="CPU measurement interval in seconds (default: 0.2)",
    )

    return parser


def handle_system(args: argparse.Namespace) -> int:
    """Execute system metrics inspection."""
    interval = getattr(args, "interval", 0.2)
    disk = getattr(args, "disk", None)
    try:
        data = get_system_health(cpu_interval=interval, target_disk=disk)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.json_mode:
        print(to_json(data))
    else:
        print(format_system_report(data))
    return 0


def handle_process(args: argparse.Namespace) -> int:
    """Execute process inspection."""
    limit = getattr(args, "limit", 10)
    sort_by = getattr(args, "sort", "cpu")
    interval = getattr(args, "interval", 0.1)
    include_idle = getattr(args, "include_idle", False)
    try:
        data = get_top_processes(
            limit=limit,
            sort_by=sort_by,
            interval=interval,
            include_idle=include_idle,
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.json_mode:
        print(to_json(data))
    else:
        print(format_process_report(data))
    return 0


def handle_git(args: argparse.Namespace) -> int:
    """Execute Git repository inspection."""
    path = getattr(args, "path", ".")
    try:
        data = get_git_status(repo_path=path)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if not data.get("is_repo"):
        if args.json_mode:
            print(to_json(data))
        else:
            print(format_git_report(data), file=sys.stderr)
        return 1

    if args.json_mode:
        print(to_json(data))
    else:
        print(format_git_report(data))
    return 0


def handle_all(args: argparse.Namespace) -> int:
    """Execute combined inspection."""
    interval = getattr(args, "interval", 0.2)
    limit = getattr(args, "limit", 5)
    sort_by = getattr(args, "sort", "cpu")
    path = getattr(args, "path", ".")
    try:
        try:
            valid_interval = float(interval) if interval is not None else 0.2
            if math.isnan(valid_interval) or math.isinf(valid_interval):
                valid_interval = 0.2
        except (ValueError, TypeError):
            valid_interval = 0.2

        system_data = get_system_health(cpu_interval=valid_interval)
        proc_interval = min(valid_interval, 0.1) if valid_interval > 0 else 0.0
        proc_data = get_top_processes(
            limit=limit,
            sort_by=sort_by,
            interval=proc_interval,
            include_idle=False,
        )
        git_data = get_git_status(repo_path=path)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    combined = {
        "system": system_data,
        "processes": proc_data,
        "git": git_data,
    }

    if args.json_mode:
        print(to_json(combined))
    else:
        print(format_all_report(combined))
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point for sysmon CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    cmd = args.command
    if cmd in ("system", "sys", "metrics") or cmd is None:
        # Default action when no subcommand is specified is 'system'
        return handle_system(args)
    elif cmd in ("process", "processes", "ps", "top"):
        return handle_process(args)
    elif cmd in ("git", "repo"):
        return handle_git(args)
    elif cmd in ("all", "summary", "overview"):
        return handle_all(args)
    else:
        parser.print_help(sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

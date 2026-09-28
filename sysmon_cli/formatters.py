"""Formatters for human-readable terminal output and structured JSON."""

import json
import math
from typing import Any, Dict
from sysmon_cli.units import render_progress_bar


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Safely convert any value to a finite float, returning default on invalid/NaN/Inf."""
    if val is None:
        return default
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return default
        return f
    except (ValueError, TypeError):
        return default


def format_system_report(data: Dict[str, Any]) -> str:
    """Format system metrics (CPU, RAM, Swap, Disk) for terminal display."""
    lines = []
    lines.append("================================================================================")
    lines.append("                            SYSTEM HEALTH MONITOR                               ")
    lines.append("================================================================================")

    # Host & Platform Info
    plat = data.get("platform") or {}
    if plat:
        sys_name = plat.get("system") or "Unknown"
        release = plat.get("release") or ""
        hostname = plat.get("hostname") or ""
        uptime = plat.get("uptime_seconds")
        if uptime is not None:
            try:
                uptime_val = float(uptime)
                if not (math.isnan(uptime_val) or math.isinf(uptime_val)) and uptime_val >= 0:
                    uptime_int = int(uptime_val)
                    uptime_str = f"{uptime_int // 3600}h {(uptime_int % 3600) // 60}m"
                else:
                    uptime_str = "N/A"
            except (ValueError, TypeError, OverflowError):
                uptime_str = "N/A"
        else:
            uptime_str = "N/A"
        lines.append(f" Host: {hostname} | OS: {sys_name} {release} | Uptime: {uptime_str}")
        lines.append("-" * 80)

    # CPU Section
    cpu = data.get("cpu") or {}
    usage = _safe_float(cpu.get("usage_percent"), 0.0)
    logical = cpu.get("count_logical") or 1
    physical = cpu.get("count_physical") or logical
    freq = cpu.get("frequency_mhz")
    freq_curr = None
    if isinstance(freq, dict):
        raw_curr = freq.get("current")
        if raw_curr is not None:
            try:
                fc = float(raw_curr)
                if not (math.isnan(fc) or math.isinf(fc)):
                    freq_curr = round(fc, 1)
            except (ValueError, TypeError):
                freq_curr = None
    freq_str = f" @ {freq_curr} MHz" if freq_curr is not None else ""
    bar = render_progress_bar(usage, width=24)
    lines.append(f" CPU Usage:    {bar}  {usage:5.1f}%  ({physical}C/{logical}T{freq_str})")

    # RAM Section
    mem = data.get("memory") or {}
    mem_usage = _safe_float(mem.get("percent"), 0.0)
    mem_used = mem.get("used_human") or "0 B"
    mem_total = mem.get("total_human") or "0 B"
    mem_avail = mem.get("available_human") or "0 B"
    mem_bar = render_progress_bar(mem_usage, width=24)
    lines.append(f" RAM Usage:    {mem_bar}  {mem_usage:5.1f}%  ({mem_used} / {mem_total}, {mem_avail} avail)")

    # Swap Section
    swap = data.get("swap") or {}
    if swap and swap.get("total_bytes", 0) > 0:
        sw_usage = _safe_float(swap.get("percent"), 0.0)
        sw_used = swap.get("used_human") or "0 B"
        sw_total = swap.get("total_human") or "0 B"
        sw_bar = render_progress_bar(sw_usage, width=24)
        lines.append(f" Swap Usage:   {sw_bar}  {sw_usage:5.1f}%  ({sw_used} / {sw_total})")

    lines.append("-" * 80)

    # Disk Section
    lines.append(" DISK PARTITIONS:")
    lines.append(f"  {'Device':<12} {'Mountpoint':<18} {'Type':<8} {'Total':<10} {'Used':<10} {'Free':<10} {'Usage':<8} Bar")
    lines.append(f"  {'-'*10:<12} {'-'*16:<18} {'-'*6:<8} {'-'*8:<10} {'-'*8:<10} {'-'*8:<10} {'-'*6:<8} {'-'*15}")

    disks = data.get("disk") or []
    if disks:
        for d in disks:
            dev = str(d.get("device") or "N/A")[:11]
            mnt = str(d.get("mountpoint") or "N/A")[:17]
            fstype = str(d.get("fstype") or "N/A")[:7]
            total = str(d.get("total_human") or "0 B")
            used = str(d.get("used_human") or "0 B")
            free = str(d.get("free_human") or "0 B")
            pct = _safe_float(d.get("percent"), 0.0)
            d_bar = render_progress_bar(pct, width=15)
            lines.append(f"  {dev:<12} {mnt:<18} {fstype:<8} {total:<10} {used:<10} {free:<10} {pct:5.1f}%  {d_bar}")
    else:
        lines.append("  No disk partitions detected.")

    lines.append("================================================================================")
    return "\n".join(lines)


def format_process_report(data: Dict[str, Any]) -> str:
    """Format active process table for terminal display."""
    lines = []
    sort_by = str(data.get("sort_by", "cpu")).upper()
    count = data.get("count", 0)
    limit = data.get("limit", 10)

    lines.append("================================================================================")
    lines.append(f"                      TOP PROCESSES (RANKED BY {sort_by})                       ")
    lines.append("================================================================================")
    lines.append(f" Showing top {count} of {limit} requested processes")
    lines.append("-" * 80)
    lines.append(f"  {'PID':>7}  {'Process Name':<28} {'CPU %':>7} {'Mem %':>7}  {'Memory (RSS)':>12}  {'Status':<10}")
    lines.append(f"  {'-'*7:>7}  {'-'*28:<28} {'-'*7:>7} {'-'*7:>7}  {'-'*12:>12}  {'-'*10:<10}")

    procs = data.get("processes") or []
    if not procs:
        lines.append("  No matching active processes found.")
    else:
        for p in procs:
            pid = str(p.get("pid") if p.get("pid") is not None else 0)
            name = str(p.get("name") or "unknown")[:28]
            cpu_val = _safe_float(p.get("cpu_percent"), 0.0)
            mem_val = _safe_float(p.get("memory_percent"), 0.0)
            cpu = f"{cpu_val:5.1f}%"
            mem = f"{mem_val:5.1f}%"
            rss = str(p.get("memory_rss_human") or "0 B")
            status = str(p.get("status") or "unknown")[:10]
            lines.append(f"  {pid:>7}  {name:<28} {cpu:>7} {mem:>7}  {rss:>12}  {status:<10}")

    lines.append("================================================================================")
    return "\n".join(lines)


def format_git_report(data: Dict[str, Any]) -> str:
    """Format Git status report for terminal display."""
    lines = []
    if not data.get("is_repo"):
        err = data.get("error", "Not a Git repository")
        path = data.get("path", ".")
        return f"Error: {err}\nTarget directory: {path}"

    lines.append("================================================================================")
    lines.append("                            GIT REPOSITORY STATUS                               ")
    lines.append("================================================================================")
    lines.append(f" Repository Root:  {data.get('root_dir', 'N/A')}")
    lines.append(f" Current Branch:   {data.get('branch', 'unknown')}")

    is_clean = data.get("is_clean", True)
    changes = data.get("total_changes", 0)
    status_label = "CLEAN (Working tree clean)" if is_clean else f"DIRTY ({changes} uncommitted changes)"
    lines.append(f" Working Status:   {status_label}")

    if not is_clean:
        staged = data.get("staged_count", 0)
        unstaged = data.get("unstaged_count", 0)
        untracked = data.get("untracked_count", 0)
        lines.append(f" Changes Breakdown: {staged} staged, {unstaged} unstaged, {untracked} untracked")

    commit = data.get("latest_commit")
    if commit and isinstance(commit, dict) and commit.get("hash"):
        c_hash = commit.get("hash", "")
        msg = commit.get("message", "")
        author = commit.get("author_name", "")
        r_date = commit.get("relative_date", "")
        detail_parts = []
        if r_date:
            detail_parts.append(r_date)
        if author:
            detail_parts.append(f"by {author}")
        details_str = f" ({' by '.join(detail_parts) if len(detail_parts) > 1 else detail_parts[0]})" if detail_parts else ""
        lines.append(f" Latest Commit:    [{c_hash}] {msg}{details_str}")
    else:
        lines.append(" Latest Commit:    No commits recorded")

    upstream = data.get("upstream")
    if upstream:
        tracking = upstream.get("tracking_branch", "")
        ahead = upstream.get("ahead", 0)
        behind = upstream.get("behind", 0)
        sync_status = "Up to date"
        if ahead > 0 and behind > 0:
            sync_status = f"Diverged (+{ahead}, -{behind})"
        elif ahead > 0:
            sync_status = f"Ahead by {ahead} commits"
        elif behind > 0:
            sync_status = f"Behind by {behind} commits"
        lines.append(f" Remote Upstream:  {tracking} ({sync_status})")

    lines.append("================================================================================")
    return "\n".join(lines)


def format_all_report(data: Dict[str, Any]) -> str:
    """Format combined system, process, and Git status report."""
    parts = []
    if "system" in data:
        parts.append(format_system_report(data["system"]))
    if "processes" in data:
        parts.append(format_process_report(data["processes"]))
    if "git" in data:
        parts.append(format_git_report(data["git"]))
    return "\n\n".join(parts)


def to_json(data: Any, indent: int = 2) -> str:
    """Serialize dictionary or list to formatted JSON."""
    return json.dumps(data, indent=indent, default=str)

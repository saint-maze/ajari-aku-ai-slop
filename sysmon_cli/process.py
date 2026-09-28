"""Process inspection and resource ranking."""

from contextlib import nullcontext
import math
import time
from typing import Any, Dict, List, Optional
import psutil

from sysmon_cli.units import format_bytes


def get_top_processes(
    limit: int = 10,
    sort_by: str = "cpu",
    interval: float = 0.1,
    include_idle: bool = False,
) -> Dict[str, Any]:
    """Retrieve top resource-consuming processes sorted by CPU or memory.

    Args:
        limit: Number of processes to return (default: 10). Must be non-negative.
        sort_by: Metric to sort by ('cpu' or 'memory'/'mem').
        interval: Sampling interval for CPU measurement (default: 0.1s).
        include_idle: Whether to include System Idle Process (PID 0) on Windows.

    Returns:
        Dictionary containing sort metadata and the list of ranked processes.
    """
    if limit is not None and limit < 0:
        raise ValueError(f"Limit must be non-negative, got {limit}.")

    normalized_sort = sort_by.lower() if sort_by else "cpu"
    if normalized_sort in ("mem", "memory", "memory_percent", "rss"):
        sort_key = "memory"
    elif normalized_sort in ("cpu", "cpu%", "cpu_percent"):
        sort_key = "cpu"
    else:
        raise ValueError(f"Invalid sort key: '{sort_by}'. Must be 'cpu' or 'memory'.")

    if limit == 0:
        return {
            "sort_by": sort_key,
            "limit": 0,
            "count": 0,
            "processes": [],
        }

    try:
        valid_interval = max(0.0, float(interval)) if interval is not None else 0.0
        if math.isnan(valid_interval) or math.isinf(valid_interval):
            valid_interval = 0.0
    except (ValueError, TypeError):
        valid_interval = 0.0

    collected: List[Dict[str, Any]] = []

    if valid_interval > 0:
        procs_to_query: List[psutil.Process] = []
        for proc in psutil.process_iter():
            try:
                pid = proc.pid
                if not include_idle and pid == 0:
                    continue
                try:
                    proc.cpu_percent(interval=None)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                procs_to_query.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        time.sleep(valid_interval)
        iterator = procs_to_query
    else:
        iterator = psutil.process_iter()

    for proc in iterator:
        try:
            pid = proc.pid
            if not include_idle and pid == 0:
                continue

            cm = proc.oneshot() if hasattr(proc, "oneshot") and callable(proc.oneshot) else nullcontext()
            with cm:
                try:
                    name = proc.name() or "unknown"
                except (psutil.NoSuchProcess, psutil.ZombieProcess):
                    raise
                except Exception:
                    name = "unknown"

                try:
                    raw_cpu = float(proc.cpu_percent(interval=None))
                    cpu_pct = 0.0 if (math.isnan(raw_cpu) or math.isinf(raw_cpu)) else round(raw_cpu, 1)
                except (psutil.NoSuchProcess, psutil.ZombieProcess):
                    raise
                except Exception:
                    cpu_pct = 0.0

                try:
                    raw_mem = float(proc.memory_percent())
                    mem_pct = 0.0 if (math.isnan(raw_mem) or math.isinf(raw_mem)) else round(raw_mem, 2)
                except (psutil.NoSuchProcess, psutil.ZombieProcess):
                    raise
                except Exception:
                    mem_pct = 0.0

                try:
                    mem_info = proc.memory_info()
                    rss_bytes = max(0, int(mem_info.rss)) if mem_info else 0
                except (psutil.NoSuchProcess, psutil.ZombieProcess):
                    raise
                except Exception:
                    rss_bytes = 0

                try:
                    status = str(proc.status())
                except (psutil.NoSuchProcess, psutil.ZombieProcess):
                    raise
                except Exception:
                    status = "unknown"

                collected.append({
                    "pid": pid,
                    "name": name,
                    "cpu_percent": cpu_pct,
                    "memory_percent": mem_pct,
                    "memory_rss_bytes": rss_bytes,
                    "memory_rss_human": format_bytes(rss_bytes),
                    "status": status,
                    "_proc": proc,
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # Sort
    if sort_key == "cpu":
        collected.sort(key=lambda x: (x["cpu_percent"], x["memory_percent"], x["memory_rss_bytes"]), reverse=True)
    else:
        collected.sort(key=lambda x: (x["memory_percent"], x["memory_rss_bytes"], x["cpu_percent"]), reverse=True)

    if limit is not None:
        if limit == 0:
            top_collected: List[Dict[str, Any]] = []
        else:
            top_collected = collected[:limit]
    else:
        top_collected = collected

    # Resolve username ONLY for the top N processes (avoiding hundreds of slow Windows RPCs)
    for item in top_collected:
        proc_obj = item.pop("_proc", None)
        username = None
        if proc_obj is not None:
            try:
                username = proc_obj.username()
            except Exception:
                username = None
        item["username"] = username

    # Clean up _proc from any unselected items
    for item in collected:
        item.pop("_proc", None)

    return {
        "sort_by": sort_key,
        "limit": limit if limit is not None else len(top_collected),
        "count": len(top_collected),
        "processes": top_collected,
    }

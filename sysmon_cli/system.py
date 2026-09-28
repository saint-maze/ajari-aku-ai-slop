"""System health and metrics collection (CPU, Memory, Disk)."""

import math
import os
import platform
import time
from typing import Any, Dict, List, Optional
import psutil

from sysmon_cli.units import format_bytes


def get_cpu_metrics(interval: float = 0.2) -> Dict[str, Any]:
    """Collect real-time CPU utilization, core counts, and frequency."""
    try:
        valid_interval = max(0.0, float(interval)) if interval is not None else 0.0
        if math.isnan(valid_interval) or math.isinf(valid_interval):
            valid_interval = 0.0
    except (ValueError, TypeError):
        valid_interval = 0.0

    if valid_interval > 0:
        try:
            per_cpu_raw = psutil.cpu_percent(interval=valid_interval, percpu=True)
            per_cpu = []
            for p in per_cpu_raw:
                try:
                    f = float(p)
                    per_cpu.append(0.0 if (math.isnan(f) or math.isinf(f)) else f)
                except (ValueError, TypeError):
                    per_cpu.append(0.0)
            if per_cpu:
                usage_percent = round(float(sum(per_cpu) / len(per_cpu)), 1)
            else:
                raw_u = float(psutil.cpu_percent(interval=None))
                usage_percent = 0.0 if (math.isnan(raw_u) or math.isinf(raw_u)) else round(raw_u, 1)
        except Exception:
            try:
                raw_u = float(psutil.cpu_percent(interval=valid_interval))
                usage_percent = 0.0 if (math.isnan(raw_u) or math.isinf(raw_u)) else round(raw_u, 1)
            except Exception:
                usage_percent = 0.0
            per_cpu = []
    else:
        try:
            per_cpu_raw = psutil.cpu_percent(interval=None, percpu=True)
            per_cpu = []
            for p in per_cpu_raw:
                try:
                    f = float(p)
                    per_cpu.append(0.0 if (math.isnan(f) or math.isinf(f)) else f)
                except (ValueError, TypeError):
                    per_cpu.append(0.0)
            if per_cpu:
                usage_percent = round(float(sum(per_cpu) / len(per_cpu)), 1)
            else:
                raw_u = float(psutil.cpu_percent(interval=None))
                usage_percent = 0.0 if (math.isnan(raw_u) or math.isinf(raw_u)) else round(raw_u, 1)
        except Exception:
            usage_percent = 0.0
            per_cpu = []

    if math.isnan(usage_percent) or math.isinf(usage_percent):
        usage_percent = 0.0

    logical_cores = psutil.cpu_count(logical=True) or 1
    physical_cores = psutil.cpu_count(logical=False) or logical_cores

    freq_dict = None
    try:
        cpu_freq = psutil.cpu_freq()
        if cpu_freq:
            def _clean_freq(val: Any) -> Optional[float]:
                if val is None:
                    return None
                try:
                    f = float(val)
                    return round(f, 1) if not (math.isnan(f) or math.isinf(f)) else None
                except (ValueError, TypeError):
                    return None

            freq_dict = {
                "current": _clean_freq(cpu_freq.current),
                "min": _clean_freq(cpu_freq.min),
                "max": _clean_freq(cpu_freq.max),
            }
    except Exception:
        freq_dict = None

    load_avg = None
    if hasattr(os, "getloadavg"):
        try:
            load_avg = [
                0.0 if (math.isnan(float(x)) or math.isinf(float(x))) else round(float(x), 2)
                for x in os.getloadavg()
            ]
        except Exception:
            load_avg = None

    return {
        "usage_percent": usage_percent,
        "count_logical": logical_cores,
        "count_physical": physical_cores,
        "per_cpu_percent": per_cpu,
        "frequency_mhz": freq_dict,
        "load_average": load_avg,
    }


def get_memory_metrics() -> Dict[str, Any]:
    """Collect system RAM metrics in bytes, percentages, and human-readable units."""
    try:
        vmem = psutil.virtual_memory()
        total = max(0, int(getattr(vmem, "total", 0)))
        avail = max(0, int(getattr(vmem, "available", 0)))
        used = max(0, int(getattr(vmem, "used", 0)))
        free = max(0, int(getattr(vmem, "free", 0)))
        raw_pct = float(getattr(vmem, "percent", 0.0))
        percent = 0.0 if (math.isnan(raw_pct) or math.isinf(raw_pct)) else round(raw_pct, 2)
    except Exception:
        total, avail, used, free, percent = 0, 0, 0, 0, 0.0

    return {
        "total_bytes": total,
        "available_bytes": avail,
        "used_bytes": used,
        "free_bytes": free,
        "percent": percent,
        "total_human": format_bytes(total),
        "used_human": format_bytes(used),
        "available_human": format_bytes(avail),
        "free_human": format_bytes(free),
    }


def get_swap_metrics() -> Dict[str, Any]:
    """Collect swap memory metrics."""
    try:
        swap = psutil.swap_memory()
        total = max(0, int(swap.total))
        used = max(0, int(swap.used))
        free = max(0, int(swap.free))
        raw_pct = float(swap.percent)
        percent = 0.0 if (math.isnan(raw_pct) or math.isinf(raw_pct)) else round(raw_pct, 2)
        return {
            "total_bytes": total,
            "used_bytes": used,
            "free_bytes": free,
            "percent": percent,
            "total_human": format_bytes(total),
            "used_human": format_bytes(used),
            "free_human": format_bytes(free),
        }
    except Exception:
        return {
            "total_bytes": 0,
            "used_bytes": 0,
            "free_bytes": 0,
            "percent": 0.0,
            "total_human": "0 B",
            "used_human": "0 B",
            "free_human": "0 B",
        }


def get_disk_metrics(target_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Collect disk partition statistics in bytes, percentages, and human-readable units."""
    results: List[Dict[str, Any]] = []

    if target_path:
        # Inspect specific path
        try:
            usage = psutil.disk_usage(target_path)
            raw_pct = float(usage.percent)
            pct = 0.0 if (math.isnan(raw_pct) or math.isinf(raw_pct)) else round(raw_pct, 2)
            results.append({
                "device": target_path,
                "mountpoint": target_path,
                "fstype": "N/A",
                "total_bytes": max(0, int(usage.total)),
                "used_bytes": max(0, int(usage.used)),
                "free_bytes": max(0, int(usage.free)),
                "percent": pct,
                "total_human": format_bytes(usage.total),
                "used_human": format_bytes(usage.used),
                "free_human": format_bytes(usage.free),
                "accessible": True,
            })
            return results
        except Exception:
            results.append({
                "device": target_path,
                "mountpoint": target_path,
                "fstype": "N/A",
                "total_bytes": 0,
                "used_bytes": 0,
                "free_bytes": 0,
                "percent": 0.0,
                "total_human": "0 B",
                "used_human": "0 B",
                "free_human": "0 B",
                "accessible": False,
            })
            return results

    # Inspect all partitions
    try:
        partitions = psutil.disk_partitions(all=False)
    except Exception:
        partitions = []

    seen_mounts = set()
    for part in partitions:
        mount = part.mountpoint
        if mount in seen_mounts:
            continue
        seen_mounts.add(mount)

        try:
            usage = psutil.disk_usage(mount)
            raw_pct = float(usage.percent)
            pct = 0.0 if (math.isnan(raw_pct) or math.isinf(raw_pct)) else round(raw_pct, 2)
            results.append({
                "device": part.device,
                "mountpoint": mount,
                "fstype": part.fstype,
                "total_bytes": max(0, int(usage.total)),
                "used_bytes": max(0, int(usage.used)),
                "free_bytes": max(0, int(usage.free)),
                "percent": pct,
                "total_human": format_bytes(usage.total),
                "used_human": format_bytes(usage.used),
                "free_human": format_bytes(usage.free),
                "accessible": True,
            })
        except Exception:
            # Inaccessible drives (e.g. CD-ROM, unmounted network share, permission denied)
            continue

    # Fallback if no partitions could be enumerated (e.g. some containers)
    if not results:
        drive = os.path.splitdrive(os.getcwd())[0] if platform.system() == "Windows" else ""
        fallback_root = "/" if platform.system() != "Windows" else ((drive or "C:") + "\\")
        try:
            usage = psutil.disk_usage(fallback_root)
            raw_pct = float(usage.percent)
            pct = 0.0 if (math.isnan(raw_pct) or math.isinf(raw_pct)) else round(raw_pct, 2)
            results.append({
                "device": fallback_root,
                "mountpoint": fallback_root,
                "fstype": "default",
                "total_bytes": max(0, int(usage.total)),
                "used_bytes": max(0, int(usage.used)),
                "free_bytes": max(0, int(usage.free)),
                "percent": pct,
                "total_human": format_bytes(usage.total),
                "used_human": format_bytes(usage.used),
                "free_human": format_bytes(usage.free),
                "accessible": True,
            })
        except Exception:
            pass

    return results


def get_system_health(cpu_interval: float = 0.2, target_disk: Optional[str] = None) -> Dict[str, Any]:
    """Compile comprehensive system health metrics (CPU, Memory, Swap, Disk)."""
    now = time.time()
    try:
        boot_time = psutil.boot_time()
        uptime_seconds = max(0, int(now - boot_time))
    except Exception:
        boot_time = None
        uptime_seconds = None

    return {
        "timestamp": now,
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "hostname": platform.node(),
            "uptime_seconds": uptime_seconds,
        },
        "cpu": get_cpu_metrics(interval=cpu_interval),
        "memory": get_memory_metrics(),
        "swap": get_swap_metrics(),
        "disk": get_disk_metrics(target_path=target_disk),
    }

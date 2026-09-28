"""Git repository inspection (branch, status, commits)."""

import os
import shutil
import subprocess
from typing import Any, Dict, Optional


def _run_git(args: list, cwd: str, timeout: float = 10.0) -> subprocess.CompletedProcess:
    """Run a git command safely and return CompletedProcess."""
    try:
        return subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            args=["git"] + args,
            returncode=124,
            stdout="",
            stderr="Git command timed out",
        )
    except Exception as e:
        return subprocess.CompletedProcess(
            args=["git"] + args,
            returncode=1,
            stdout="",
            stderr=str(e),
        )


def get_git_status(repo_path: str = ".") -> Dict[str, Any]:
    """Inspect Git repository status and branch.

    Returns:
        Dict with repository information if in a Git repo, or error information if not.
    """
    resolved_path = os.path.abspath(repo_path)
    if not os.path.exists(resolved_path):
        return {
            "is_repo": False,
            "error": f"Path '{repo_path}' does not exist.",
            "path": resolved_path,
        }

    # If repo_path is a file, use its parent directory for Git inspection
    target_dir = resolved_path if os.path.isdir(resolved_path) else os.path.dirname(resolved_path)

    # Verify git executable is present
    if not shutil.which("git"):
        return {
            "is_repo": False,
            "error": "Git executable not found in system PATH.",
            "path": resolved_path,
        }

    # Check if directory is inside a git working tree
    check_repo = _run_git(["rev-parse", "--is-inside-work-tree"], cwd=target_dir)
    if check_repo.returncode != 0 or check_repo.stdout.strip() != "true":
        # Check if directory is a bare repository
        check_bare = _run_git(["rev-parse", "--is-bare-repository"], cwd=target_dir)
        if check_bare.returncode == 0 and check_bare.stdout.strip() == "true":
            log_proc = _run_git(["log", "-1", "--format=%h%x1f%an%x1f%ae%x1f%ar%x1f%s"], cwd=target_dir)
            latest_commit: Optional[Dict[str, str]] = None
            if log_proc.returncode == 0 and log_proc.stdout.strip():
                raw_log = log_proc.stdout.strip()
                delim = "\x1f" if "\x1f" in raw_log else "|"
                parts = raw_log.split(delim, 4)
                latest_commit = {
                    "hash": parts[0] if len(parts) > 0 else "",
                    "author_name": parts[1] if len(parts) > 1 else "",
                    "author_email": parts[2] if len(parts) > 2 else "",
                    "relative_date": parts[3] if len(parts) > 3 else "",
                    "message": parts[4] if len(parts) > 4 else "",
                }
            return {
                "is_repo": True,
                "path": resolved_path,
                "root_dir": target_dir,
                "branch": "(bare repository)",
                "is_clean": True,
                "is_dirty": False,
                "staged_count": 0,
                "unstaged_count": 0,
                "untracked_count": 0,
                "total_changes": 0,
                "latest_commit": latest_commit,
                "upstream": None,
                "bare": True,
            }
        err_msg = check_repo.stderr.strip() or f"'{repo_path}' is not a Git repository (or any parent directory)."
        return {
            "is_repo": False,
            "error": err_msg,
            "path": resolved_path,
        }

    # Get repository root
    root_proc = _run_git(["rev-parse", "--show-toplevel"], cwd=target_dir)
    root_dir = root_proc.stdout.strip() if root_proc.returncode == 0 else target_dir

    # Get current branch
    branch_proc = _run_git(["symbolic-ref", "--short", "-q", "HEAD"], cwd=target_dir)
    if branch_proc.returncode == 0 and branch_proc.stdout.strip():
        branch = branch_proc.stdout.strip()
    else:
        # Detached HEAD or empty repository
        branch_name_proc = _run_git(["branch", "--show-current"], cwd=target_dir)
        if branch_name_proc.returncode == 0 and branch_name_proc.stdout.strip():
            branch = branch_name_proc.stdout.strip()
        else:
            rev_proc = _run_git(["rev-parse", "--short", "HEAD"], cwd=target_dir)
            if rev_proc.returncode == 0 and rev_proc.stdout.strip():
                branch = f"(detached at {rev_proc.stdout.strip()})"
            else:
                branch = "main"

    # Status porcelain
    status_proc = _run_git(["status", "--porcelain=v1"], cwd=target_dir)
    porcelain_lines = [line for line in status_proc.stdout.splitlines() if line.strip()]

    staged_count = 0
    unstaged_count = 0
    untracked_count = 0

    for line in porcelain_lines:
        if line.startswith("??"):
            untracked_count += 1
        else:
            idx = line[0] if len(line) > 0 else " "
            wt = line[1] if len(line) > 1 else " "
            if idx not in (" ", "?"):
                staged_count += 1
            if wt not in (" ", "?"):
                unstaged_count += 1

    total_changes = len(porcelain_lines)
    is_dirty = total_changes > 0
    is_clean = not is_dirty

    # Latest commit info
    log_proc = _run_git(["log", "-1", "--format=%h%x1f%an%x1f%ae%x1f%ar%x1f%s"], cwd=target_dir)
    latest_commit: Optional[Dict[str, str]] = None
    if log_proc.returncode == 0 and log_proc.stdout.strip():
        raw_log = log_proc.stdout.strip()
        delim = "\x1f" if "\x1f" in raw_log else "|"
        parts = raw_log.split(delim, 4)
        latest_commit = {
            "hash": parts[0] if len(parts) > 0 else "",
            "author_name": parts[1] if len(parts) > 1 else "",
            "author_email": parts[2] if len(parts) > 2 else "",
            "relative_date": parts[3] if len(parts) > 3 else "",
            "message": parts[4] if len(parts) > 4 else "",
        }

    # Upstream / Remote tracking branch
    upstream_proc = _run_git(["rev-parse", "--abbrev-ref", "@{u}"], cwd=target_dir)
    upstream_info: Optional[Dict[str, Any]] = None
    if upstream_proc.returncode == 0 and upstream_proc.stdout.strip():
        tracking = upstream_proc.stdout.strip()
        count_proc = _run_git(["rev-list", "--left-right", "--count", "HEAD...@{u}"], cwd=target_dir)
        ahead, behind = 0, 0
        if count_proc.returncode == 0 and count_proc.stdout.strip():
            c_parts = count_proc.stdout.strip().split()
            if len(c_parts) >= 2:
                try:
                    ahead, behind = int(c_parts[0]), int(c_parts[1])
                except ValueError:
                    pass
        upstream_info = {
            "tracking_branch": tracking,
            "ahead": ahead,
            "behind": behind,
        }

    return {
        "is_repo": True,
        "path": resolved_path,
        "root_dir": root_dir,
        "branch": branch,
        "is_clean": is_clean,
        "is_dirty": is_dirty,
        "staged_count": staged_count,
        "unstaged_count": unstaged_count,
        "untracked_count": untracked_count,
        "total_changes": total_changes,
        "latest_commit": latest_commit,
        "upstream": upstream_info,
    }

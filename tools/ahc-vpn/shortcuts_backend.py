#!/usr/bin/env python3
import subprocess
import os
import sys

ALLOWED_TARGETS = ["DE", "US"]
ALLOWED_SHORTCUTS = [f"AHC {t} {a}" for t in ALLOWED_TARGETS for a in ["Connect", "Disconnect"]]

def list_shortcuts():
    try:
        res = subprocess.run(["/usr/bin/shortcuts", "list"], capture_output=True, text=True, timeout=10)
        if res.returncode == 0:
            return res.stdout.splitlines(), None
        return [], f"shortcuts list failed: {res.stderr}"
    except subprocess.TimeoutExpired:
        return [], "shortcuts list timeout"
    except Exception as e:
        return [], str(e)

def verify_shortcuts():
    registered, err = list_shortcuts()
    if err:
        return False, err
    missing = [sc for sc in ALLOWED_SHORTCUTS if sc not in registered]
    if missing:
        return False, f"Missing shortcuts: {missing}"
    return True, None

def run_shortcut(name, time_budget=30):
    """命令発行のみ。観測は行わない。"""
    if name not in ALLOWED_SHORTCUTS:
        return {"command_completed": False, "error": "Invalid shortcut name"}

    try:
        res = subprocess.run(["/usr/bin/shortcuts", "run", name], capture_output=True, text=True, timeout=time_budget)
        if res.returncode == 0:
            return {"command_completed": True, "stdout": res.stdout.strip()}
        else:
            return {"command_completed": False, "error": res.stderr.strip()}
    except subprocess.TimeoutExpired:
        return {"command_completed": False, "error": "timeout"}
    except Exception as e:
        return {"command_completed": False, "error": str(e)}

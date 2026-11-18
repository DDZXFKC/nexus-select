#!/usr/bin/env python3
import subprocess
import os
import sys

# 同一ディレクトリ基準でモジュールを読み込む
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from status_probe import probe_status

ALLOWED_TARGETS = ["DE", "US"]
EXPECTED_SHORTCUTS = [f"AHC {t} Connect" for t in ALLOWED_TARGETS] + [f"AHC {t} Disconnect" for t in ALLOWED_TARGETS]

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
    missing = [sc for sc in EXPECTED_SHORTCUTS if sc not in registered]
    if missing:
        return False, f"Missing shortcuts: {missing}"
    return True, None

def run_shortcut(name, timeout=30):
    """実行結果を4種に区別し、終了コードだけで成功判定しない"""
    try:
        res = subprocess.run(["/usr/bin/shortcuts", "run", name], capture_output=True, text=True, timeout=timeout)
        if res.returncode == 0:
            return "COMPLETED", res.stdout.strip()
        else:
            return "COMMAND_ERROR", res.stderr.strip()
    except subprocess.TimeoutExpired:
        return "TIMEOUT", None
    except Exception as e:
        return "EXECUTION_ERROR", str(e)

def connect(target):
    if target not in ALLOWED_TARGETS:
        return {"success": False, "error": "Invalid target"}

    name = f"AHC {target} Connect"
    exec_status, exec_msg = run_shortcut(name)

    # 独自のポーリングはせず、現在の状態を1回取得するだけ
    current_probe = probe_status()
    actual_state = current_probe["profiles"].get(target, "UNKNOWN")

    return {
        "exec_result": exec_status,
        "exec_msg": exec_msg,
        "observed_state": actual_state,
        "probe_data": current_probe,
        "success": (exec_status == "COMPLETED" and actual_state == "CONNECTED")
    }

def disconnect(target):
    if target not in ALLOWED_TARGETS:
        return {"success": False, "error": "Invalid target"}

    name = f"AHC {target} Disconnect"
    exec_status, exec_msg = run_shortcut(name)

    current_probe = probe_status()
    actual_state = current_probe["profiles"].get(target, "UNKNOWN")

    return {
        "exec_result": exec_status,
        "exec_msg": exec_msg,
        "observed_state": actual_state,
        "probe_data": current_probe,
        "success": (exec_status == "COMPLETED" and actual_state == "DISCONNECTED")
    }

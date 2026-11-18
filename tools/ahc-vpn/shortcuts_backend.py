#!/usr/bin/env python3
import subprocess
import math

ALLOWED_TARGETS = ["DE", "US"]
ALLOWED_SHORTCUTS = [f"AHC {t} {a}" for t in ALLOWED_TARGETS for a in ["Connect", "Disconnect"]]

def verify_shortcuts():
    try:
        res = subprocess.run(["/usr/bin/shortcuts", "list"], capture_output=True, text=True, timeout=10)
        if res.returncode != 0:
            return False, "list_failed"
        registered = res.stdout.splitlines()
        if len(registered) != len(set(registered)):
            return False, "duplicate_shortcuts"
        missing = [sc for sc in ALLOWED_SHORTCUTS if sc not in registered]
        if missing:
            return False, f"missing: {missing}"
        return True, None
    except Exception as e:
        return False, "list_exception"

def run_shortcut(name, time_budget):
    if name not in ALLOWED_SHORTCUTS:
        return {"result_code": "REJECTED", "command_completed": False, "effect_unknown": False, "sanitized_error": "invalid_name"}

    if not isinstance(time_budget, (int, float)) or math.isnan(time_budget) or math.isinf(time_budget) or time_budget <= 0:
        return {"result_code": "REJECTED", "command_completed": False, "effect_unknown": False, "sanitized_error": "invalid_time_budget"}

    try:
        res = subprocess.run(["/usr/bin/shortcuts", "run", name], capture_output=True, text=True, timeout=time_budget)
        code = "COMPLETED" if res.returncode == 0 else "COMMAND_ERROR"
        return {
            "result_code": code,
            "command_completed": (res.returncode == 0),
            "returncode": res.returncode,
            "effect_unknown": True, # 常に不確定（監査指示通り）
            "sanitized_error": None if res.returncode == 0 else "command_error"
        }
    except subprocess.TimeoutExpired:
        return {"result_code": "TIMEOUT", "command_completed": False, "effect_unknown": True, "sanitized_error": "timeout"}
    except Exception:
        return {"result_code": "EXECUTION_ERROR", "command_completed": False, "effect_unknown": True, "sanitized_error": "execution_error"}

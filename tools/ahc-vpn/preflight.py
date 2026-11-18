#!/usr/bin/env python3
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shortcuts_backend import verify_shortcuts
from status_probe import probe_status

def run_preflight():
    result = {
        "shortcuts_registered": False,
        "diagnostic_ready": False,
        "profile_status_verified": False,
        "recovery_ready": False, # 常にfalse
        "mutation_ready": False, # 常にfalse
        "probe_data": None,
        "errors": []
    }

    try:
        sc_ok, sc_err = verify_shortcuts()
        if sc_ok:
            result["shortcuts_registered"] = True
            result["diagnostic_ready"] = True
        else:
            result["errors"].append(f"Shortcuts verification failed: {sc_err}")

        probe = probe_status()
        result["probe_data"] = probe

        if not probe.get("errors"):
            # エラーなく観測できた場合のみtrue（状態がUNKNOWNでも）
            result["profile_status_verified"] = True

    except Exception as e:
        result["errors"].append(f"Preflight exception: {str(e)}")

    return result

if __name__ == "__main__":
    print(json.dumps(run_preflight(), indent=2))

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
        "diagnostic_executable": False,
        "diagnostic_completed": False,
        "diagnostic_partial": False,
        "profile_status_verified": False, # 常にfalse
        "recovery_ready": False, # 常にfalse
        "mutation_ready": False, # 常にfalse
        "probe_data": None,
        "errors": []
    }

    sc_ok, sc_err = verify_shortcuts()
    if sc_ok:
        result["shortcuts_registered"] = True
        result["diagnostic_executable"] = True
    else:
        result["errors"].append(f"shortcuts: {sc_err}")
        return result

    try:
        probe = probe_status()
        result["probe_data"] = probe
        if not probe.get("errors"):
            result["diagnostic_completed"] = True
        else:
            result["diagnostic_partial"] = True
    except Exception as e:
        result["errors"].append(f"probe_exception: {str(e)}")

    return result

if __name__ == "__main__":
    print(json.dumps(run_preflight(), indent=2))

#!/usr/bin/env python3
import json
import os
import sys

# スクリプト自身のディレクトリ基準でモジュールを検索
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shortcuts_backend import verify_shortcuts
from status_probe import probe_status

def run_preflight():
    result = {
        "shortcuts_registered": False,
        "diagnostic_ready": False,
        "profile_status_verified": False,
        "recovery_ready": False,
        "mutation_ready": False,
        "probe_data": None,
        "errors": []
    }

    try:
        # 1. ショートカット登録確認
        sc_ok, sc_err = verify_shortcuts()
        if sc_ok:
            result["shortcuts_registered"] = True
            result["diagnostic_ready"] = True
        else:
            result["errors"].append(f"Shortcuts verification failed: {sc_err}")

        # 2. 状態取得テスト
        probe = probe_status()
        result["probe_data"] = probe

        if probe.get("errors"):
            result["errors"].append(f"Probe reported errors: {probe['errors']}")
        else:
            result["profile_status_verified"] = True

            # 状態が確定 verified=True の場合のみ復旧準備完了とする
            if probe.get("verified"):
                result["recovery_ready"] = True

        # preflight単独では切替を許可しない（watchdog確認とarmはControllerが管理）
        result["mutation_ready"] = False

    except Exception as e:
        result["errors"].append(f"Preflight exception: {str(e)}")

    return result

if __name__ == "__main__":
    output = run_preflight()
    print(json.dumps(output, indent=2))

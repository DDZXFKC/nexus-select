#!/usr/bin/env python3
import json
import sys

# 同一ディレクトリからインポートを想定
sys.path.insert(0, '.')
from shortcuts_backend import verify_shortcuts
from status_probe import probe_status

def run_preflight() -> dict:
    """
    読み取り専用の事前検査を実行し、結果をJSONで返す。
    切替（VPNの接続・切断）は一切行わない。
    """
    result = {
        "shortcuts_registered": False,
        "status_probe_result": "UNKNOWN",
        "ready": False,
        "errors": []
    }

    try:
        # 1. ショートカット登録確認
        if verify_shortcuts():
            result["shortcuts_registered"] = True
        else:
            result["errors"].append("Required shortcuts are not registered or accessible.")

        # 2. 現在の状態取得テスト
        status = probe_status()
        result["status_probe_result"] = status

        # status_probeがUNKNOWNを返した場合、機能しているが状態が不明なだけなのでエラーにはしない
        # ただし、エラーハンドリングで例外が飛んでいないか確認

        # 判定: ショートカットが登録されていれば、状態に関わらず準備完了とする
        if result["shortcuts_registered"]:
            result["ready"] = True

    except Exception as e:
        result["errors"].append(f"Preflight exception: {str(e)}")
        result["ready"] = False

    return result

if __name__ == "__main__":
    # CLIから実行された場合はJSONを出力
    output = run_preflight()
    print(json.dumps(output, indent=2))

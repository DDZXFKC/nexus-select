#!/usr/bin/env python3
import subprocess
import json
from typing import Dict, Any

# 期待されるショートカット名
EXPECTED_SHORTCUTS = [
    "AHC DE Connect",
    "AHC DE Disconnect",
    "AHC US Connect",
    "AHC US Disconnect"
]

def list_shortcuts() -> list:
    """登録されているショートカットのリストを取得する"""
    try:
        result = subprocess.run(
            ["/usr/bin/shortcuts", "list"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return []
        return result.stdout.splitlines()
    except subprocess.TimeoutExpired:
        return []
    except Exception:
        return []

def verify_shortcuts() -> bool:
    """必須ショートカットがすべて登録されているか確認する"""
    registered = list_shortcuts()
    return all(sc in registered for sc in EXPECTED_SHORTCUTS)

def run_shortcut(name: str, timeout: int = 30) -> Dict[str, Any]:
    """
    ショートカットを実行する。
    タイムアウト時は終了コードで成功判定せず、status_probeで実状態を確認する。
    """
    try:
        subprocess.run(
            ["/usr/bin/shortcuts", "run", name],
            capture_output=True, text=True, timeout=timeout
        )
        return {"executed": True, "timeout": False}
    except subprocess.TimeoutExpired:
        # タイムアウトしてもバックグラウンドで接続処理が続いている可能性がある
        return {"executed": False, "timeout": True}
    except Exception as e:
        return {"executed": False, "timeout": False, "error": str(e)}

def connect(target: str = "DE") -> Dict[str, Any]:
    """指定ターゲット(DE/US)のVPN接続ショートカットを実行する"""
    from status_probe import probe_status

    name = f"AHC {target.upper()} Connect"
    exec_result = run_shortcut(name)

    # 実行後の状態を確認
    current_status = probe_status()
    expected_status = f"{target.upper()}_CONNECTED"

    if current_status == expected_status:
        return {"success": True, "status": current_status}
    else:
        # 状態が一致しない場合は次の操作を禁止するため失敗を返す
        return {
            "success": False,
            "status": current_status,
            "message": f"Connection mismatch: expected {expected_status}, got {current_status}"
        }

def disconnect(target: str = "DE") -> Dict[str, Any]:
    """指定ターゲット(DE/US)のVPN切断ショートカットを実行する"""
    from status_probe import probe_status

    name = f"AHC {target.upper()} Disconnect"
    exec_result = run_shortcut(name)

    # 実行後の状態を確認
    current_status = probe_status()

    if current_status == "DISCONNECTED":
        return {"success": True, "status": current_status}
    else:
        return {
            "success": False,
            "status": current_status,
            "message": f"Disconnection failed or still connected: {current_status}"
        }

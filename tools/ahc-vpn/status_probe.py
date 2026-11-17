#!/usr/bin/env python3
import subprocess
import re
from typing import Optional

# 期待される出口IP（オーナー指定値）
EXPECTED_IPS = {
    "DE": "187.40.57.138",
    "US": "2.56.191.90"
}

def get_default_gateway_interface() -> Optional[str]:
    """デフォルトルートのインターフェースを取得する"""
    try:
        result = subprocess.run(
            ["/sbin/netstat", "-rn"],
            capture_output=True, text=True, timeout=5
        )
        # default 行を探す
        for line in result.stdout.splitlines():
            if line.startswith("default"):
                parts = line.split()
                if len(parts) >= 6:
                    return parts[5]  # インターフェース名
        return None
    except Exception:
        return None

def get_interface_ip(interface: str, timeout: int = 10) -> Optional[str]:
    """指定インターフェースを経由した出口IPを取得する"""
    try:
        result = subprocess.run(
            ["/usr/bin/curl", "--interface", interface, "-s", "https://api.ipify.org"],
            capture_output=True, text=True, timeout=timeout
        )
        ip = result.stdout.strip()
        # 簡易的なIPフォーマット検証
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
            return ip
        return None
    except Exception:
        return None

def get_active_utun_interfaces() -> list:
    """アクティブなutunインターフェースのリストを取得する"""
    try:
        result = subprocess.run(
            ["/sbin/ifconfig", "-l"],
            capture_output=True, text=True, timeout=5
        )
        interfaces = result.stdout.split()
        return [iface for iface in interfaces if iface.startswith("utun")]
    except Exception:
        return []

def probe_status() -> str:
    """
    複合判定でVPN接続状態を返す。
    戻り値: DE_CONNECTED / US_CONNECTED / DISCONNECTED / UNKNOWN
    """
    # 1. デフォルトゲートウェイの確認
    default_iface = get_default_gateway_interface()
    active_utuns = get_active_utun_interfaces()

    if not active_utuns:
        return "DISCONNECTED"

    # 確認すべきインターフェース（デフォルトルートがutunなら優先）
    target_ifaces = []
    if default_iface and default_iface.startswith("utun"):
        target_ifaces.append(default_iface)

    # その他のutunも追加
    for utun in active_utuns:
        if utun not in target_ifaces:
            target_ifaces.append(utun)

    # 2. 各utunインターフェース経由の出口IPを確認
    for iface in target_ifaces:
        ip = get_interface_ip(iface)
        if ip:
            for target, expected_ip in EXPECTED_IPS.items():
                if ip == expected_ip:
                    return f"{target}_CONNECTED"

    # utunは存在するが期待するIPが取得できない場合は不明
    return "UNKNOWN"

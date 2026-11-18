#!/usr/bin/env python3
import subprocess
import ipaddress
import os

# 実IPを公開リポジトリにハードコードしない（環境変数から取得）
EXPECTED_IPS = {
    "DE": os.environ.get("AHC_VPN_DE_IP"),
    "US": os.environ.get("AHC_VPN_US_IP")
}

def parse_route_output(output):
    for line in output.splitlines():
        if "interface:" in line:
            return line.split("interface:")[1].strip()
    return None

def get_default_route_iface():
    try:
        res = subprocess.run(["/sbin/route", "-n", "get", "default"], capture_output=True, text=True, timeout=5)
        if res.returncode != 0:
            return None, "route command failed"
        return parse_route_output(res.stdout), None
    except Exception as e:
        return None, str(e)

def get_active_utun_interfaces():
    try:
        res = subprocess.run(["/sbin/ifconfig", "-l"], capture_output=True, text=True, timeout=5)
        if res.returncode != 0:
            return [], "ifconfig -l failed"
        interfaces = res.stdout.split()
        return [iface for iface in interfaces if iface.startswith("utun")], None
    except Exception as e:
        return [], str(e)

def is_iface_active(iface):
    try:
        res = subprocess.run(["/sbin/ifconfig", iface], capture_output=True, text=True, timeout=5)
        if res.returncode != 0:
            return False, "ifconfig failed"
        return "status: active" in res.stdout, None
    except Exception as e:
        return False, str(e)

def get_exit_ip(iface):
    try:
        res = subprocess.run(["/usr/bin/curl", "--interface", iface, "-s", "https://api.ipify.org"], capture_output=True, text=True, timeout=10)
        if res.returncode != 0 or not res.stdout:
            return None, "curl failed or empty response"
        ip_str = res.stdout.strip()
        ipaddress.ip_address(ip_str) # 例外を発生させることでIPフォーマットを検証
        return ip_str, None
    except Exception as e:
        return None, str(e)

def probe_status():
    evidence = []
    errors = []
    profiles = {"DE": "UNKNOWN", "US": "UNKNOWN"}
    unmanaged_vpn = "UNKNOWN"
    exit_country = "UNKNOWN"
    verified = False
    network_reachable = False

    iface, err = get_default_route_iface()
    if err:
        errors.append(f"route: {err}")
    else:
        evidence.append(f"Default route interface: {iface}")
        if iface and iface.startswith("utun"):
            active, a_err = is_iface_active(iface)
            if a_err:
                errors.append(f"ifconfig active check: {a_err}")
            elif active:
                unmanaged_vpn = "CONNECTED"
                evidence.append(f"Interface {iface} is active.")

                # 外部IP確認（補助検証）
                ip, ip_err = get_exit_ip(iface)
                if ip_err:
                    errors.append(f"curl: {ip_err}")
                    network_reachable = False
                else:
                    network_reachable = True
                    evidence.append(f"Exit IP via {iface}: {ip}")

                    # 期待値と照合してプロファイルを確定
                    for p, expected_ip in EXPECTED_IPS.items():
                        if expected_ip and ip == expected_ip:
                            profiles[p] = "CONNECTED"
                            verified = True
                            # exit_country 等の追加判定があればここで実施
                            break
            else:
                evidence.append(f"Interface {iface} is inactive.")
                unmanaged_vpn = "DISCONNECTED"
                profiles["DE"] = "DISCONNECTED"
                profiles["US"] = "DISCONNECTED"
                verified = True
        else:
            # デフォルトルートが utun ではない場合（en0等）
            evidence.append("Default route is not utun.")
            utuns, u_err = get_active_utun_interfaces()
            if u_err:
                errors.append(f"ifconfig -l: {u_err}")
            elif not utuns:
                # utunが1つも存在しなければ、完全に未接続と断定
                unmanaged_vpn = "DISCONNECTED"
                profiles["DE"] = "DISCONNECTED"
                profiles["US"] = "DISCONNECTED"
                verified = True
            else:
                evidence.append(f"utun interfaces exist: {utuns}. Possible split tunnel.")
                # スプリットトンネル等の可能性があるため UNKNOWN を維持

    return {
        "profiles": profiles,
        "unmanaged_vpn": unmanaged_vpn,
        "exit_country": exit_country,
        "network_reachable": network_reachable,
        "evidence": evidence,
        "errors": errors,
        "verified": verified
    }

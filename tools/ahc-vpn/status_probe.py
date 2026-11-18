#!/usr/bin/env python3
import subprocess
import os
import sys

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

def get_iface_status(iface):
    try:
        res = subprocess.run(["/sbin/ifconfig", iface], capture_output=True, text=True, timeout=5)
        if res.returncode != 0:
            return "unknown", "ifconfig failed"
        if "status: active" in res.stdout:
            return "active", None
        elif "status: inactive" in res.stdout:
            return "inactive", None
        return "unknown", None
    except Exception as e:
        return "unknown", str(e)

def probe_status():
    # 監査指示により、プロファイル別状態は常にUNKNOWNで確定しない
    profiles = {"DE": "UNKNOWN", "US": "UNKNOWN"}
    verified = False
    errors = []
    tunnel_observation = {
        "default_route_iface": None,
        "utun_interfaces": []
    }

    iface, err = get_default_route_iface()
    if err:
        errors.append(f"route: {err}")
    else:
        tunnel_observation["default_route_iface"] = iface

    utuns, u_err = get_active_utun_interfaces()
    if u_err:
        errors.append(f"ifconfig -l: {u_err}")
    else:
        tunnel_observation["utun_interfaces"] = []
        for ut in utuns:
            status, s_err = get_iface_status(ut)
            if s_err:
                errors.append(f"ifconfig {ut}: {s_err}")
            tunnel_observation["utun_interfaces"].append({"name": ut, "status": status})

    return {
        "profiles": profiles,
        "verified": verified,
        "tunnel_observation": tunnel_observation,
        "errors": errors
    }

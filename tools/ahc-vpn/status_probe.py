#!/usr/bin/env python3
import subprocess
import re
import datetime
import math

def _now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def list_utun_interfaces(deadline):
    interfaces = []
    err = None
    try:
        res = subprocess.run(["/sbin/ifconfig", "-l"], capture_output=True, text=True, timeout=max(0.1, deadline))
        if res.returncode != 0:
            err = "ifconfig -l failed"
        elif not res.stdout.strip():
            err = "ifconfig -l empty stdout"
        else:
            for iface in res.stdout.split():
                if re.match(r"^utun\d+$", iface):
                    interfaces.append(iface)
    except subprocess.TimeoutExpired:
        err = "ifconfig timeout"
    except Exception as e:
        err = str(e)
    return interfaces, err

def get_default_route_iface(deadline):
    try:
        res = subprocess.run(["/sbin/route", "-n", "get", "default"], capture_output=True, text=True, timeout=max(0.1, deadline))
        if res.returncode != 0:
            return None, "route failed"
        ifaces = []
        for line in res.stdout.splitlines():
            if "interface:" in line:
                val = line.split("interface:")[1].strip()
                if val: ifaces.append(val)
        if len(ifaces) == 0: return None, "route interface missing"
        if len(ifaces) > 1: return None, "route multiple interfaces"
        return ifaces[0], None
    except Exception as e:
        return None, str(e)

def parse_status(stdout):
    for line in stdout.splitlines():
        if "status:" in line:
            val = line.split("status:")[1].strip().lower()
            if val == "active": return "active", None
            if val == "inactive": return "inactive", None
            return "unknown", f"unrecognized status: {val}"
    return "unknown", "status line missing"

def probe_status(time_budget=10.0):
    start = datetime.datetime.now()
    errors = []
    profiles = {"DE": "UNKNOWN", "US": "UNKNOWN"}

    def remaining():
        return max(0.0, time_budget - (datetime.datetime.now() - start).total_seconds())

    route_iface, r_err = get_default_route_iface(remaining())
    if r_err: errors.append(f"route: {r_err}")

    utuns, u_err = list_utun_interfaces(remaining())
    if u_err: errors.append(f"utun_list: {u_err}")

    utun_states = []
    for ut in utuns:
        if remaining() <= 0: errors.append("budget_exhausted"); break
        try:
            res = subprocess.run(["/sbin/ifconfig", ut], capture_output=True, text=True, timeout=remaining())
            st, s_err = parse_status(res.stdout)
            if s_err: errors.append(f"{ut}: {s_err}")
            utun_states.append({"name": ut, "status": st})
        except Exception as e:
            errors.append(f"{ut}: {str(e)}")
            utun_states.append({"name": ut, "status": "unknown"})

    return {
        "profiles": profiles,
        "unmanaged_vpn": "UNKNOWN",
        "source": "local_probe",
        "observed_at": _now_iso(),
        "completeness": "PARTIAL" if errors else "FULL",
        "tunnel_observation": {
            "default_route_iface": route_iface,
            "utun_interfaces": utun_states
        },
        "errors": errors
    }

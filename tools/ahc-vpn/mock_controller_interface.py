#!/usr/bin/env python3
import json
from preflight import run_preflight

def mock_connect(target):
    return {"status": "MOCKED", "target": target, "action": "connect", "mutation_allowed": False}

def mock_disconnect(target):
    return {"status": "MOCKED", "target": target, "action": "disconnect", "mutation_allowed": False}

if __name__ == "__main__":
    print(json.dumps({"preflight": run_preflight(), "mock_actions": "available"}, indent=2))

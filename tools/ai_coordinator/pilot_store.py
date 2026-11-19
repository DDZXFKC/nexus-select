"""Local durable synthetic pilot, not the authoritative GitHub dispatcher."""
import fcntl
import json
import os
import pathlib
import tempfile
from contextlib import contextmanager
from core import Coordinator

@contextmanager
def transaction(path, contract):
    path = pathlib.Path(path)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with open(str(path)+'.lock','a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        snapshot = json.loads(path.read_text()) if path.exists() else None
        coordinator = Coordinator(contract, snapshot)
        yield coordinator
        fd, tmp = tempfile.mkstemp(prefix='.state-', dir=str(path.parent))
        try:
            with os.fdopen(fd,'w') as stream:
                json.dump(coordinator.state,stream,sort_keys=True)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(tmp,path)
            directory = os.open(str(path.parent),os.O_RDONLY)
            try: os.fsync(directory)
            finally: os.close(directory)
        finally:
            if os.path.exists(tmp): os.unlink(tmp)

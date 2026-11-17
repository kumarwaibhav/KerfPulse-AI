"""Research resource admission and crash-safe evidence, independent of serving."""
import ctypes
import json
import os
import re
from pathlib import Path
import subprocess
import tempfile
import time


def atomic_json(path, value):
    encoded = json.dumps(value, indent=2, allow_nan=False)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', dir=path.parent, encoding='utf-8', delete=False) as file:
        temporary = Path(file.name)
        file.write(encoded)
        file.flush()
        os.fsync(file.fileno())
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def snapshot():
    import psutil
    memory = psutil.virtual_memory()
    commit = memory.available + psutil.swap_memory().free
    if os.name == 'nt':
        class Status(ctypes.Structure):
            _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong)] + [(k, ctypes.c_ulonglong) for k in
                ('total_physical', 'available_physical', 'total_page', 'available_page', 'total_virtual', 'available_virtual', 'extended')]
        status = Status()
        status.length = ctypes.sizeof(status)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            raise OSError('Cannot inspect Windows commit headroom')
        commit = status.available_page
    command = ['nvidia-smi', '--query-gpu=name,memory.free,memory.used,temperature.gpu,driver_version', '--format=csv,noheader,nounits']
    fields = subprocess.check_output(command, text=True, timeout=10).strip().splitlines()[0].split(', ')
    limit = 80
    try:
        reported = subprocess.check_output(['nvidia-smi', '-q', '-d', 'TEMPERATURE'], text=True, timeout=10)
        absolute = re.search(r'GPU Slowdown Temp\s*:\s*(\d+) C', reported)
        if absolute:
            limit = min(80, float(absolute.group(1))-5)
    except (subprocess.SubprocessError, ValueError):
        pass
    return {'at': time.time(), 'ram_available': memory.available, 'commit_available': commit,
            'gpu_name': fields[0], 'gpu_free': float(fields[1])*2**20, 'gpu_used': float(fields[2])*2**20,
            'temperature': float(fields[3]), 'driver': fields[4], 'thermal_limit': limit}


def admission_reasons(state, gpu=True):
    reasons = []
    if state['ram_available'] < 2*2**30: reasons.append('ram')
    if state['commit_available'] < 4*2**30: reasons.append('commit')
    if gpu and state['gpu_free'] < 2**30: reasons.append('vram')
    if gpu and state['temperature'] >= state['thermal_limit']: reasons.append('temperature')
    return reasons


class ResourceGuard:
    def __init__(self, directory, gpu=True):
        self.path = Path(directory)/'resources.jsonl'
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.gpu = gpu
        self.last = 0

    def check(self, force=False):
        if not force and time.monotonic()-self.last < 5:
            return
        while True:
            state = snapshot()
            reasons = admission_reasons(state, self.gpu)
            with self.path.open('a', encoding='utf-8') as file:
                file.write(json.dumps({**state, 'pause_reasons': reasons})+'\n')
            if not reasons:
                self.last = time.monotonic()
                return
            print(json.dumps({'state':'resource_pause', 'reasons':reasons}), flush=True)
            time.sleep(5)


class ExperimentLock:
    def __init__(self, path): self.path = Path(path)

    def __enter__(self):
        import psutil
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            owner = json.loads(self.path.read_text())
            if psutil.pid_exists(owner['pid']):
                raise RuntimeError('Another experiment owns the GPU lock')
            self.path.unlink()
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, 'w') as file: json.dump({'pid': os.getpid()}, file)
        return self

    def __exit__(self, *_): self.path.unlink(missing_ok=True)

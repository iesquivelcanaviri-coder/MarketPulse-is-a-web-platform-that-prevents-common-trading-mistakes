"""
============================================================
CORE - MATLAB BRIDGE
============================================================
Framework mapping: API → this service → MATLAB `marketpulse_bridge.m` → JSON response.
MATLAB is lazy so a missing installation never blocks Django startup.
"""
import json,subprocess,tempfile
from pathlib import Path
from django.conf import settings
from .exceptions import MatlabUnavailable
def run_matlab_operation(operation,payload):
    if not settings.MATLAB_ENABLED: raise MatlabUnavailable('MATLAB disabled. Set MATLAB_ENABLED=True to use it.')
    with tempfile.TemporaryDirectory() as d:
        inp=Path(d)/'input.json'; out=Path(d)/'output.json'; inp.write_text(json.dumps(payload),encoding='utf-8')
        expr=f"addpath('{Path(settings.MATLAB_DIR).as_posix()}'); marketpulse_bridge('{inp.as_posix()}','{out.as_posix()}','{operation}');"
        try: subprocess.run([settings.MATLAB_COMMAND,'-batch',expr],check=True,capture_output=True,text=True,timeout=120)
        except Exception as exc: raise MatlabUnavailable(f'MATLAB execution failed: {exc}') from exc
        if not out.exists(): raise MatlabUnavailable('MATLAB produced no output file.')
        return json.loads(out.read_text(encoding='utf-8'))

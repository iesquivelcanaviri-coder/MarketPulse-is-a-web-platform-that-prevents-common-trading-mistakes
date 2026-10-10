"""
============================================================
CORE - MATLAB BRIDGE
============================================================
Framework mapping: API → this service → MATLAB `marketpulse_bridge.m` → JSON response.
MATLAB is lazy so a missing installation never blocks Django startup.
"""

# ============================================================
# 1. IMPORTS
# ============================================================

import json,subprocess,tempfile  # IMPORTS: brings in JSON conversion, external-process execution, and temporary-file tools from Python.
from pathlib import Path  # IMPORT: imports the Path class so file and folder paths can be represented as objects.
from django.conf import settings  # DJANGO FRAMEWORK: imports the current Django project settings so this file can read MATLAB configuration.
from .exceptions import MatlabUnavailable  # RELATIVE IMPORT: imports our custom exception from the current core package.

# ============================================================
# 2. MATLAB OPERATION FUNCTION
# ============================================================

def run_matlab_operation(operation,payload):  # FUNCTION: defines reusable behaviour; operation and payload are parameters supplied by the caller.
    if not settings.MATLAB_ENABLED: raise MatlabUnavailable('MATLAB disabled. Set MATLAB_ENABLED=True to use it.')  # CONDITIONAL + BOOLEAN + EXCEPTION: stops execution when MATLAB is disabled in Django settings.
    with tempfile.TemporaryDirectory() as d:  # CONTEXT MANAGER: creates a temporary folder and automatically removes it when this block finishes.
        inp=Path(d)/'input.json'; out=Path(d)/'output.json'; inp.write_text(json.dumps(payload),encoding='utf-8')  # VARIABLES + PATHS + FILE I/O + SERIALIZATION: creates input/output paths and converts the Python payload into JSON for MATLAB.
        expr=f"addpath('{Path(settings.MATLAB_DIR).as_posix()}'); marketpulse_bridge('{inp.as_posix()}','{out.as_posix()}','{operation}');"  # F-STRING: dynamically builds the MATLAB command using settings, file paths, and the requested operation.
        try: subprocess.run([settings.MATLAB_COMMAND,'-batch',expr],check=True,capture_output=True,text=True,timeout=120)  # TRY + FUNCTION CALL + LIST + KEYWORD ARGUMENTS: starts MATLAB as another process and waits for the MATLAB command to finish.
        except Exception as exc: raise MatlabUnavailable(f'MATLAB execution failed: {exc}') from exc  # EXCEPTION HANDLING + EXCEPTION CHAINING: converts a MATLAB/process failure into the project's MatlabUnavailable error while keeping the original cause.
        if not out.exists(): raise MatlabUnavailable('MATLAB produced no output file.')  # CONDITIONAL + METHOD CALL + EXCEPTION: checks that MATLAB actually created the expected output JSON file.
        return json.loads(out.read_text(encoding='utf-8'))  # RETURN + FILE I/O + DESERIALIZATION: reads MATLAB's JSON result, converts it into Python data, and sends it back to the caller.
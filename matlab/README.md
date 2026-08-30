# MATLAB Integration

Framework mapping: `core/matlab_bridge.py` writes JSON, launches MATLAB with `-batch`, calls `marketpulse_bridge.m`, then reads JSON output. Django still starts when MATLAB is disabled.

Enable in `.env`:
```env
MATLAB_ENABLED=True
MATLAB_COMMAND=matlab
```

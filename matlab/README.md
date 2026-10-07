# MATLAB Integration

## Overview

The `matlab/` folder contains the optional MATLAB analytical component of **MarketPulse**.

MarketPulse is primarily a Django web application. Django manages the user interface, database, application logic, API communication and the main user workflows.

MATLAB is included as a separate analytical engine for selected numerical calculations.

This means MATLAB does **not** replace Django and it does **not** run the MarketPulse website. Instead, Django can send data to MATLAB when a MATLAB calculation is required, receive the calculated result, and then continue processing or displaying that result inside the MarketPulse application.


---

## Why This Folder Exists

The purpose of the MATLAB integration is to demonstrate how MarketPulse can connect a web application to a separate numerical-computing environment.

The integration supports three types of MATLAB operations:

1. Risk calculations
2. Statistical analysis
3. Market-regime analysis

The MATLAB files are therefore part of the application's analytical layer rather than the presentation layer.


---

## Framework Integration

The MATLAB integration follows this structure:

```text
MarketPulse User Interface
        ↓
Django View / Application Logic
        ↓
core/matlab_bridge.py
        ↓
JSON input file
        ↓
MATLAB
        ↓
marketpulse_bridge.m
        ↓
Selected MATLAB function
        ↓
JSON output file
        ↓
core/matlab_bridge.py
        ↓
Django
        ↓
MarketPulse User Interface
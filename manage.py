#!/usr/bin/env python
"""
============================================================
MARKETPULSE - DJANGO COMMAND ENTRY POINT
============================================================
Framework mapping: starts Django commands and loads marketpulse/settings.py.
"""
import os, sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE','marketpulse.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()

#!/usr/bin/env bash
# ============================================================
# RENDER BUILD SCRIPT
# ============================================================

# 1. SCRIPT INTERPRETER
# The first line selects Bash through the environment's PATH.
# Concept: a shebang identifies the interpreter when this file
# is executed directly.

# 2. ERROR HANDLING
# I stop this sequence if one of the following commands fails.
# Concept: a shell option controls script execution.
set -o errexit

# 3. UPDATE THE PACKAGE INSTALLER
# I run pip using the selected Python interpreter.
# Concepts: command arguments, module execution (-m) and flags.
python -m pip install --upgrade pip

# 4. INSTALL PROJECT DEPENDENCIES
# pip reads requirements.txt and installs its listed packages.
# This makes dependencies such as Django available.
# Concept: one file supplies input to another tool.
python -m pip install -r requirements.txt

# 5. COLLECT STATIC FILES
# manage.py passes this command to Django.
# Django gathers static assets into the configured STATIC_ROOT.
# --noinput prevents interactive prompts during deployment.
# Concept: command delegation and configuration-driven behaviour.
python manage.py collectstatic --noinput

# 6. APPLY DATABASE MIGRATIONS
# Django applies pending migrations to the configured database.
# This prepares database structures needed by my models.
# Concept: sequential execution and persistent database changes.
python manage.py migrate
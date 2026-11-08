"""WSGI entry point for PythonAnywhere.

Paste this file's contents into the Web tab's WSGI configuration file and
replace USERNAME / SECRET with your values.
"""
import os
import sys

path = "/home/USERNAME/math14"
if path not in sys.path:
    sys.path.insert(0, path)

os.environ.setdefault("MATH14_SECRET", "REPLACE_WITH_A_LONG_RANDOM_STRING")
os.environ.setdefault("MATH14_SECURE", "1")

from app import create_app  # noqa: E402

application = create_app()
